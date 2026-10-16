"""
AUDITRA Data Pipeline & Telemetry Ingestion Tests
Owner: Amulya Dongre

Validates Section 4 Telemetry and Scenario Data Contracts:
1. Valid TelemetryRecord creation with verified units.
2. Invariant: available_at >= event_time.
3. Rejection of negative actual power or energy.
4. ForecastRecord creation and timezone parsing.
5. DispatchRecord creation and curtailment limit validation.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas import (
    TelemetryRecord,
    ForecastRecord,
    DispatchRecord,
    SensorProvenance,
    EvidenceQuality
)


class TestTelemetryDataContracts:

    def test_valid_telemetry_record_creation(self):
        """Standard 15-minute telemetry interval record is valid."""
        rec = TelemetryRecord(
            event_time=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            available_at=datetime(2026, 6, 15, 12, 1, 30, tzinfo=timezone.utc),  # 90s SCADA poll delay
            block_id="INV-01",
            actual_power_mw=11.2,
            actual_energy_mwh=2.8,  # 11.2 * 0.25
            poa_irradiance_clean_w_per_m2=950.0,
            primary_pyranometer_w_per_m2=955.0,
            reference_pyranometer_w_per_m2=948.0,
            module_temp_celsius=42.0,
            inverter_internal_temp_celsius=52.0,
            availability_ratio=1.0,
            active_alarms=[],
            sensor_quality=EvidenceQuality.VALIDATED,
            provenance=SensorProvenance.INVERTER_SCADA
        )
        assert rec.actual_power_mw == 11.2
        assert rec.actual_energy_mwh == 2.8
        assert rec.available_at >= rec.event_time

    def test_telemetry_negative_power_rejected(self):
        """Physical solar generation cannot produce negative power."""
        with pytest.raises(ValidationError):
            TelemetryRecord(
                event_time=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                available_at=datetime(2026, 6, 15, 12, 5, 0, tzinfo=timezone.utc),
                block_id="INV-01",
                actual_power_mw=-1.5,  # Negative power!
                actual_energy_mwh=0.0
            )

    def test_telemetry_available_before_event_rejected(self):
        """Telemetry record cannot become available before the interval event occurs."""
        with pytest.raises(ValidationError) as exc_info:
            TelemetryRecord(
                event_time=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                available_at=datetime(2026, 6, 15, 11, 59, 0, tzinfo=timezone.utc),  # Available 1 min prior!
                block_id="INV-01",
                actual_power_mw=10.0,
                actual_energy_mwh=2.5
            )
        assert "cannot precede" in str(exc_info.value)

    def test_forecast_record_valid(self):
        """Day-ahead forecast record validates correctly."""
        f_rec = ForecastRecord(
            event_time=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            available_at=datetime(2026, 6, 14, 23, 0, 0, tzinfo=timezone.utc),  # Day ahead at 23:00
            block_id="PLANT",
            forecast_power_mw=45.0,
            forecast_energy_mwh=11.25,
            expected_poa_irradiance_w_per_m2=980.0,
            model_version="DA-FORECAST-V1.0"
        )
        assert f_rec.forecast_power_mw == 45.0
        assert f_rec.available_at < f_rec.event_time

    def test_dispatch_record_valid(self):
        """Dispatch constraint record validates correctly."""
        d_rec = DispatchRecord(
            event_time=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            available_at=datetime(2026, 6, 15, 11, 30, 0, tzinfo=timezone.utc),
            curtailment_active=True,
            dispatch_limit_mw=30.0,
            curtailment_reason="Grid Transmission Capacity Constraint"
        )
        assert d_rec.curtailment_active is True
        assert d_rec.dispatch_limit_mw == 30.0
