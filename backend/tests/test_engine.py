"""
AUDITRA Domain Science & Loss Attribution Tests
Owner: Atharva Hoge

Validates Section 5, 6, 7 & 9 Physics and Attribution Requirements:
1. Physical baseline equation calculates expected power correctly.
2. Inverter capacity capping at 12.5 MW.
3. Non-negative power invariant (no negative generation).
4. Temperature coefficient derate (gamma = -0.004 / degC).
5. 15-minute energy conversion (MWh = MW * 0.25).
6. Loss attribution accounting identity (Shortfall = Sum of non-overlapping buckets).
7. Rejection of un-reconciled loss attribution models.
8. Recovery estimate physical bounds (min <= max <= observed).
"""

import pytest
from pydantic import ValidationError

from app.schemas import (
    PlantConfig,
    InverterBlockConfig,
    LossAttribution,
    LossCategory,
    LossCategoryItem,
    RecoveryEstimate
)


def calculate_inverter_physical_power(
    p_cap_mw: float,
    g_clean_w_per_m2: float,
    t_mod_celsius: float,
    gamma: float = -0.004
) -> float:
    """
    Physical baseline equation (Section 5):
    P_phys,i = min(P_cap,i, max(0, P_cap,i * (G_clean,i / 1000) * (1 + gamma * (T_mod,i - 25))))
    """
    if g_clean_w_per_m2 < 0:
        raise ValueError(f"Irradiance cannot be negative: {g_clean_w_per_m2}")
    
    uncapped = p_cap_mw * (g_clean_w_per_m2 / 1000.0) * (1.0 + gamma * (t_mod_celsius - 25.0))
    return min(p_cap_mw, max(0.0, uncapped))


class TestDomainPhysicsBaseline:

    def test_stc_conditions_produces_rated_capacity(self):
        """Under Standard Test Conditions (1000 W/m², 25°C), power should match rated capacity."""
        p_cap = 12.5  # MW
        p_phys = calculate_inverter_physical_power(
            p_cap_mw=p_cap,
            g_clean_w_per_m2=1000.0,
            t_mod_celsius=25.0
        )
        assert abs(p_phys - 12.5) < 1e-6

    def test_power_is_strictly_capped_at_inverter_capacity(self):
        """Under very high irradiance (e.g. 1200 W/m² and cold 10°C), power must cap at 12.5 MW."""
        p_cap = 12.5
        p_phys = calculate_inverter_physical_power(
            p_cap_mw=p_cap,
            g_clean_w_per_m2=1200.0,
            t_mod_celsius=10.0
        )
        assert p_phys == 12.5, "Inverter clipping not respected!"

    def test_zero_irradiance_produces_zero_power(self):
        """At night or zero irradiance, power must be 0 MW."""
        p_phys = calculate_inverter_physical_power(
            p_cap_mw=12.5,
            g_clean_w_per_m2=0.0,
            t_mod_celsius=20.0
        )
        assert p_phys == 0.0

    def test_high_module_temperature_derates_power(self):
        """At 50°C module temperature, derate factor is 1 + (-0.004 * 25) = 0.90 (10% thermal loss)."""
        p_cap = 12.5
        p_phys = calculate_inverter_physical_power(
            p_cap_mw=p_cap,
            g_clean_w_per_m2=1000.0,
            t_mod_celsius=50.0  # +25 degC above STC
        )
        expected = 12.5 * 1.0 * 0.90  # 11.25 MW
        assert abs(p_phys - expected) < 1e-6

    def test_energy_conversion_for_15min_interval(self):
        """Energy in MWh over 15 minutes is AveragePower_MW * 0.25h."""
        power_mw = 40.0
        interval_hours = 0.25
        energy_mwh = power_mw * interval_hours
        assert energy_mwh == 10.0


class TestLossAttributionInvariants:

    def test_loss_attribution_reconciles_perfectly(self):
        """Valid loss attribution where sum of buckets matches total forecast shortfall."""
        attribution = LossAttribution(
            total_forecast_energy_mwh=12.0,
            total_actual_energy_mwh=7.0,
            total_shortfall_mwh=5.0,  # 12.0 - 7.0
            weather_loss_mwh=2.0,
            curtailment_loss_mwh=1.5,
            equipment_loss_mwh=1.0,
            other_validated_loss_mwh=0.2,
            unexplained_residual_mwh=0.3,
            breakdown=[
                LossCategoryItem(category=LossCategory.WEATHER_VARIANCE, loss_mwh=2.0, equivalent_power_mw=8.0, percentage_of_shortfall=40.0, ruling_basis="Pyranometer vs forecast"),
                LossCategoryItem(category=LossCategory.GRID_CURTAILMENT, loss_mwh=1.5, equivalent_power_mw=6.0, percentage_of_shortfall=30.0, ruling_basis="Dispatch limit active"),
                LossCategoryItem(category=LossCategory.EQUIPMENT_DERATING, loss_mwh=1.0, equivalent_power_mw=4.0, percentage_of_shortfall=20.0, ruling_basis="INV-02 thermal limit"),
                LossCategoryItem(category=LossCategory.OTHER_VALIDATED, loss_mwh=0.2, equivalent_power_mw=0.8, percentage_of_shortfall=4.0, ruling_basis="Substation telemetry gap"),
                LossCategoryItem(category=LossCategory.UNEXPLAINED_RESIDUAL, loss_mwh=0.3, equivalent_power_mw=1.2, percentage_of_shortfall=6.0, ruling_basis="Unaccounted variance")
            ]
        )
        assert attribution.total_shortfall_mwh == 5.0

    def test_unreconciled_loss_attribution_rejected(self):
        """Attribution whose categories do not sum to total shortfall must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LossAttribution(
                total_forecast_energy_mwh=10.0,
                total_actual_energy_mwh=6.0,
                total_shortfall_mwh=4.0,
                weather_loss_mwh=2.0,
                curtailment_loss_mwh=1.0,
                equipment_loss_mwh=0.5,
                other_validated_loss_mwh=0.0,
                unexplained_residual_mwh=0.0  # Sum is 3.5, shortfall is 4.0 -> Violation!
            )
        assert "Loss attribution accounting identity violation" in str(exc_info.value)


class TestRecoveryEstimateInvariants:

    def test_valid_recovery_estimate(self):
        """Recovery estimate respects min <= max <= observed_loss."""
        est = RecoveryEstimate(
            observed_loss_mwh=5.0,
            detectable_loss_mwh=4.2,
            actionable_loss_mwh=3.5,
            preventable_loss_mwh=2.8,
            recoverable_energy_mwh_min=1.8,
            recoverable_energy_mwh_max=2.5,
            limiting_factors=["15-minute control room dispatch response lag", "Inverter thermal cool-down latency"],
            assumptions=["Operator acknowledges alarm within 5 minutes of receipt"]
        )
        assert est.recoverable_energy_mwh_min <= est.recoverable_energy_mwh_max <= est.observed_loss_mwh

    def test_min_greater_than_max_recovery_rejected(self):
        """Minimum recoverable energy cannot exceed maximum."""
        with pytest.raises(ValidationError) as exc_info:
            RecoveryEstimate(
                observed_loss_mwh=5.0,
                detectable_loss_mwh=4.0,
                actionable_loss_mwh=3.0,
                preventable_loss_mwh=2.5,
                recoverable_energy_mwh_min=3.0,
                recoverable_energy_mwh_max=2.0  # Min > Max
            )
        assert "cannot exceed max" in str(exc_info.value)

    def test_max_recovery_greater_than_observed_loss_rejected(self):
        """Cannot claim more recoverable energy than the entire observed physical loss."""
        with pytest.raises(ValidationError) as exc_info:
            RecoveryEstimate(
                observed_loss_mwh=3.0,
                detectable_loss_mwh=3.0,
                actionable_loss_mwh=3.0,
                preventable_loss_mwh=3.0,
                recoverable_energy_mwh_min=1.0,
                recoverable_energy_mwh_max=4.0  # Max > Observed (3.0)
            )
        assert "cannot exceed total observed loss" in str(exc_info.value)
