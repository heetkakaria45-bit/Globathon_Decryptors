"""
AUDITRA Shared Domain Schemas & API Contracts
Owner: Heet Kakaria (Tech Lead)

This module defines typed Pydantic models for the entire AUDITRA platform.
All four team members integrate against these shared contracts.

Invariants enforced:
- Explicit physical engineering units in field names and docstrings.
- Timezone-aware UTC normalization for all temporal fields.
- Non-negative physical quantities (power, irradiance, energy).
- Clear separation between sensor telemetry, evidence provenance, and forensic inferences.
- JSON serializability without untyped dicts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============================================================================
# Core Enums
# ============================================================================

class HypothesisId(str, Enum):
    """The six competing forensic hypotheses evaluated by AUDITRA."""
    H1_EQUIPMENT_DERATING = "H1_EQUIPMENT_DERATING"
    H2_WEATHER_DROP = "H2_WEATHER_DROP"
    H3_GRID_CURTAILMENT = "H3_GRID_CURTAILMENT"
    H4_SENSOR_DRIFT = "H4_SENSOR_DRIFT"
    H5_FORECAST_BIAS = "H5_FORECAST_BIAS"
    H6_UNEXPLAINED_RESIDUAL = "H6_UNEXPLAINED_RESIDUAL"


class HypothesisStatus(str, Enum):
    """Forensic status of a hypothesis under evaluation."""
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class EvidenceQuality(str, Enum):
    """Quality and validation state of an evidence record."""
    VALIDATED = "VALIDATED"
    SUSPECT = "SUSPECT"
    DEGRADED = "DEGRADED"
    MISSING = "MISSING"


class SensorProvenance(str, Enum):
    """Source authority and provenance for ingested telemetry."""
    PRIMARY_PYRANOMETER = "PRIMARY_PYRANOMETER"
    SECONDARY_PYRANOMETER = "SECONDARY_PYRANOMETER"
    SATELLITE_NOWCAST = "SATELLITE_NOWCAST"
    INVERTER_SCADA = "INVERTER_SCADA"
    WEATHER_STATION = "WEATHER_STATION"
    GRID_DISPATCH_SYSTEM = "GRID_DISPATCH_SYSTEM"
    FORECAST_ENGINE = "FORECAST_ENGINE"


class AlarmSeverity(str, Enum):
    """Severity level of telemetry equipment alarms."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class LossCategory(str, Enum):
    """Mutually exclusive loss categories for non-overlapping attribution."""
    WEATHER_VARIANCE = "WEATHER_VARIANCE"
    GRID_CURTAILMENT = "GRID_CURTAILMENT"
    EQUIPMENT_DERATING = "EQUIPMENT_DERATING"
    OTHER_VALIDATED = "OTHER_VALIDATED"
    UNEXPLAINED_RESIDUAL = "UNEXPLAINED_RESIDUAL"


# ============================================================================
# Helper Base Model for Timezone Normalization
# ============================================================================

class UtcModel(BaseModel):
    """Base model ensuring all datetime fields are timezone-aware and normalized to UTC."""
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True
    )


def ensure_utc_datetime(v: Any) -> datetime:
    """Validate that datetime is timezone-aware and convert to UTC."""
    if isinstance(v, str):
        v = datetime.fromisoformat(v.replace("Z", "+00:00"))
    if not isinstance(v, datetime):
        raise ValueError(f"Expected datetime or ISO string, got {type(v)}")
    if v.tzinfo is None:
        raise ValueError(f"Naive datetime is rejected: '{v}'. Timestamps must be timezone-aware.")
    return v.astimezone(timezone.utc)


# ============================================================================
# Plant and Hardware Configurations
# ============================================================================

class InverterBlockConfig(BaseModel):
    """Configuration for an individual inverter block (e.g. 12.5 MW AC)."""
    block_id: str = Field(..., description="Unique block identifier, e.g. 'INV-01'")
    rated_capacity_mw: float = Field(12.5, gt=0, description="Rated AC capacity in MW")
    temperature_coeff_gamma: float = Field(-0.004, description="Power temp coefficient per degree Celsius")
    reference_temp_celsius: float = Field(25.0, description="STC reference module temperature in Celsius")


class PlantConfig(BaseModel):
    """Model for Helios-1 Solar Park or similar utility-scale solar asset."""
    plant_id: str = Field("HELIOS-1", description="Asset identifier")
    name: str = Field("Helios-1 Solar Park", description="Human-readable plant name")
    total_capacity_mw: float = Field(50.0, gt=0, description="Total plant AC rated capacity in MW")
    telemetry_interval_minutes: int = Field(15, gt=0, description="Telemetry interval in minutes (default 15m)")
    interval_duration_hours: float = Field(0.25, gt=0, description="Telemetry interval duration in hours (0.25h = 15m)")
    inverter_blocks: List[InverterBlockConfig] = Field(
        default_factory=lambda: [
            InverterBlockConfig(block_id=f"INV-0{i}") for i in range(1, 5)
        ],
        min_length=1,
        description="Collection of inverter blocks comprising the plant"
    )

    @model_validator(mode="after")
    def validate_total_capacity(self) -> PlantConfig:
        sum_blocks = sum(b.rated_capacity_mw for b in self.inverter_blocks)
        if abs(sum_blocks - self.total_capacity_mw) > 1e-3:
            raise ValueError(
                f"Sum of inverter block capacities ({sum_blocks} MW) does not match total plant capacity ({self.total_capacity_mw} MW)"
            )
        return self


# ============================================================================
# Telemetry, Forecast & Dispatch Records
# ============================================================================

class TelemetryRecord(UtcModel):
    """
    15-minute telemetry interval record for an inverter block or whole plant.
    Preserves both event_time and available_at for historical time-locked replay.
    """
    event_time: datetime = Field(..., description="When the physical event occurred (UTC)")
    available_at: datetime = Field(..., description="When the telemetry reached the control room (UTC)")
    block_id: str = Field(..., description="Inverter block identifier or 'PLANT' for aggregate")
    
    # Power & Energy (Measured)
    actual_power_mw: float = Field(..., ge=0, description="Interval average measured AC power in MW")
    actual_energy_mwh: float = Field(..., ge=0, description="Interval measured energy in MWh (actual_power_mw * 0.25)")
    
    # Irradiance & Temperatures
    poa_irradiance_clean_w_per_m2: Optional[float] = Field(
        None, ge=0, description="Clean, validated Plane-of-Array irradiance in W/m²"
    )
    primary_pyranometer_w_per_m2: Optional[float] = Field(
        None, ge=0, description="Primary sensor raw irradiance in W/m²"
    )
    reference_pyranometer_w_per_m2: Optional[float] = Field(
        None, ge=0, description="Independent reference sensor irradiance in W/m²"
    )
    module_temp_celsius: Optional[float] = Field(
        None, description="Average module temperature in degrees Celsius"
    )
    inverter_internal_temp_celsius: Optional[float] = Field(
        None, description="Inverter cabinet internal temperature in degrees Celsius"
    )
    
    # Operational Status
    availability_ratio: float = Field(1.0, ge=0.0, le=1.0, description="Inverter availability [0.0 - 1.0]")
    active_alarms: List[str] = Field(default_factory=list, description="Active alarms during the interval")
    sensor_quality: EvidenceQuality = Field(EvidenceQuality.VALIDATED, description="Quality indicator for this record")
    provenance: SensorProvenance = Field(SensorProvenance.INVERTER_SCADA, description="Provenance source")

    @field_validator("event_time", "available_at", mode="before")
    @classmethod
    def parse_utc(cls, v: Any) -> datetime:
        return ensure_utc_datetime(v)

    @model_validator(mode="after")
    def validate_temporal_order(self) -> TelemetryRecord:
        if self.available_at < self.event_time:
            raise ValueError(
                f"Information availability time ({self.available_at}) cannot precede physical event time ({self.event_time})"
            )
        return self


class ForecastRecord(UtcModel):
    """
    Day-ahead power and irradiance forecast for a 15-minute interval.
    """
    event_time: datetime = Field(..., description="Target physical interval timestamp (UTC)")
    available_at: datetime = Field(..., description="When the forecast was published/locked (UTC)")
    block_id: str = Field("PLANT", description="Inverter block identifier or 'PLANT'")
    forecast_power_mw: float = Field(..., ge=0, description="Forecasted AC power in MW")
    forecast_energy_mwh: float = Field(..., ge=0, description="Forecasted AC energy in MWh")
    expected_poa_irradiance_w_per_m2: Optional[float] = Field(None, ge=0, description="Forecasted POA irradiance W/m²")
    model_version: str = Field("DA-FORECAST-V1.0", description="Forecasting model identifier")

    @field_validator("event_time", "available_at", mode="before")
    @classmethod
    def parse_utc(cls, v: Any) -> datetime:
        return ensure_utc_datetime(v)


class DispatchRecord(UtcModel):
    """
    Grid operator dispatch constraint or curtailment setpoint for an interval.
    """
    event_time: datetime = Field(..., description="Target physical interval timestamp (UTC)")
    available_at: datetime = Field(..., description="When the dispatch instruction was received (UTC)")
    curtailment_active: bool = Field(False, description="True if a grid curtailment order was active")
    dispatch_limit_mw: float = Field(50.0, ge=0, description="Maximum allowable injection into grid in MW")
    curtailment_reason: Optional[str] = Field(None, description="Stated grid reason (e.g. 'Transmission Overload')")

    @field_validator("event_time", "available_at", mode="before")
    @classmethod
    def parse_utc(cls, v: Any) -> datetime:
        return ensure_utc_datetime(v)


# ============================================================================
# Forensic Evidence & Hypotheses
# ============================================================================

class EvidenceRecord(UtcModel):
    """
    Traceable forensic evidence item with strict temporal availability and provenance.
    """
    evidence_id: str = Field(..., description="Unique evidence ID, e.g. 'EV-2026-1017-001'")
    event_time: datetime = Field(..., description="When the observed physical phenomenon occurred (UTC)")
    available_at: datetime = Field(..., description="When this evidence became knowable to control/audit (UTC)")
    source: SensorProvenance = Field(..., description="Sensor or system of origin")
    quality: EvidenceQuality = Field(EvidenceQuality.VALIDATED, description="Quality classification")
    metric_name: str = Field(..., description="Parameter observed, e.g. 'pyranometer_drift_pct'")
    metric_value: float = Field(..., description="Numeric value of observed metric")
    unit: str = Field(..., description="Physical unit, e.g. 'W/m²', 'MW', '%', 'degC'")
    block_id: Optional[str] = Field(None, description="Associated block ID if localized")
    description: str = Field(..., description="Forensic description of what this evidence proves or disproves")

    @field_validator("event_time", "available_at", mode="before")
    @classmethod
    def parse_utc(cls, v: Any) -> datetime:
        return ensure_utc_datetime(v)

    @model_validator(mode="after")
    def validate_temporal_order(self) -> EvidenceRecord:
        if self.available_at < self.event_time:
            raise ValueError(
                f"Evidence availability ({self.available_at}) cannot precede event time ({self.event_time})"
            )
        return self


class HypothesisResult(BaseModel):
    """
    Forensic evaluation result for one of the six competing hypotheses.
    """
    hypothesis_id: HypothesisId = Field(..., description="Which hypothesis was evaluated")
    title: str = Field(..., description="Human-readable title, e.g. 'H1: Inverter Thermal Derating'")
    status: HypothesisStatus = Field(..., description="SUPPORTED, CONTRADICTED, INCONCLUSIVE, or INSUFFICIENT_DATA")
    confidence_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Calibrated evidence score [0.0 - 1.0] if defensible method exists"
    )
    ruling_criteria: str = Field(..., description="Deterministic physical/operational rule used for determination")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence records that support this")
    contradicting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence records that contradict this")
    missing_evidence: List[str] = Field(default_factory=list, description="Missing telemetry or records that prevented ruling")
    summary: str = Field(..., description="Forensic narrative explaining this hypothesis ruling")


# ============================================================================
# Non-Overlapping Loss Attribution & Recoverability
# ============================================================================

class LossCategoryItem(BaseModel):
    """Attributed loss breakdown for a single category."""
    category: LossCategory = Field(..., description="The non-overlapping loss bucket")
    loss_mwh: float = Field(..., ge=0.0, description="Attributed energy shortfall in MWh")
    equivalent_power_mw: float = Field(..., ge=0.0, description="Equivalent average power in MW over interval")
    percentage_of_shortfall: float = Field(..., ge=0.0, le=100.0, description="Share of total forecast shortfall")
    ruling_basis: str = Field(..., description="Accounting rule or sequential precedence basis applied")


class LossAttribution(BaseModel):
    """
    Strict non-overlapping loss attribution reconciling the forecast shortfall:
    Forecast Energy - Actual Energy = Total Shortfall
    Total Shortfall = Weather + Curtailment + Equipment + Other + Unexplained Residual
    """
    total_forecast_energy_mwh: float = Field(..., ge=0, description="Day-ahead forecasted generation in MWh")
    total_actual_energy_mwh: float = Field(..., ge=0, description="Measured actual generation in MWh")
    total_shortfall_mwh: float = Field(..., ge=0, description="Eligible shortfall: max(0, Forecast - Actual) MWh")
    
    # Categorical breakdown
    weather_loss_mwh: float = Field(0.0, ge=0, description="Shortfall from lower-than-forecast irradiance")
    curtailment_loss_mwh: float = Field(0.0, ge=0, description="Shortfall from active grid dispatch limits")
    equipment_loss_mwh: float = Field(0.0, ge=0, description="Shortfall from hardware derating/trips")
    other_validated_loss_mwh: float = Field(0.0, ge=0, description="Shortfall from other confirmed external factors")
    unexplained_residual_mwh: float = Field(0.0, ge=0, description="Shortfall that cannot be accounted for by valid evidence")

    breakdown: List[LossCategoryItem] = Field(
        default_factory=list, description="Detailed itemized breakdown per category"
    )
    precedence_order: List[LossCategory] = Field(
        default_factory=lambda: [
            LossCategory.WEATHER_VARIANCE,
            LossCategory.GRID_CURTAILMENT,
            LossCategory.EQUIPMENT_DERATING,
            LossCategory.OTHER_VALIDATED,
            LossCategory.UNEXPLAINED_RESIDUAL
        ],
        description="Sequential attribution order applied to eliminate double-counting"
    )

    @model_validator(mode="after")
    def validate_accounting_identity(self) -> LossAttribution:
        """Enforces that allocated losses sum exactly to total shortfall within numerical tolerance."""
        allocated_sum = (
            self.weather_loss_mwh +
            self.curtailment_loss_mwh +
            self.equipment_loss_mwh +
            self.other_validated_loss_mwh +
            self.unexplained_residual_mwh
        )
        if abs(allocated_sum - self.total_shortfall_mwh) > 1e-3:
            raise ValueError(
                f"Loss attribution accounting identity violation: Sum of attributed losses ({allocated_sum:.4f} MWh) "
                f"does not match total shortfall ({self.total_shortfall_mwh:.4f} MWh) within 1e-3 tolerance."
            )
        return self


class RecoveryEstimate(BaseModel):
    """
    Forensic estimate of preventable energy and reasonably recoverable generation.
    Distinguishes observed, detectable, actionable, and preventable losses.
    """
    observed_loss_mwh: float = Field(..., ge=0, description="Total observed equipment or process energy loss")
    detectable_loss_mwh: float = Field(..., ge=0, description="Loss after first valid detection threshold was crossed")
    actionable_loss_mwh: float = Field(..., ge=0, description="Loss after information was available and operational response feasible")
    preventable_loss_mwh: float = Field(..., ge=0, description="Portion of loss that could physically have been averted")
    
    # Bounded range
    recoverable_energy_mwh_min: float = Field(..., ge=0, description="Conservative lower bound of recoverable energy MWh")
    recoverable_energy_mwh_max: float = Field(..., ge=0, description="Upper bound under ideal operational intervention MWh")
    
    limiting_factors: List[str] = Field(
        default_factory=list,
        description="Operational barriers (e.g., dispatch cooldown, crew travel time, cooling thermal inertia)"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Explicit assumptions made in the recovery counterfactual calculation"
    )

    @model_validator(mode="after")
    def validate_recovery_bounds(self) -> RecoveryEstimate:
        if self.recoverable_energy_mwh_min > self.recoverable_energy_mwh_max:
            raise ValueError(
                f"recoverable_energy_mwh_min ({self.recoverable_energy_mwh_min}) cannot exceed max ({self.recoverable_energy_mwh_max})"
            )
        if self.recoverable_energy_mwh_max > self.observed_loss_mwh + 1e-3:
            raise ValueError(
                f"recoverable_energy_mwh_max ({self.recoverable_energy_mwh_max}) cannot exceed total observed loss ({self.observed_loss_mwh})"
            )
        return self


# ============================================================================
# Replay API Request & Response Contracts
# ============================================================================

class ReplayRequest(UtcModel):
    """
    Forensic time-locked replay request.
    Only evidence with available_at <= replay_time will be eligible for investigation.
    """
    scenario_id: str = Field(..., description="Scenario identifier, e.g. 'SCENARIO-01-THERMAL-TRIP'")
    replay_time: datetime = Field(..., description="Historical perspective timestamp (UTC)")
    include_evidence_log: bool = Field(True, description="Whether to include full eligible evidence list in response")

    @field_validator("replay_time", mode="before")
    @classmethod
    def parse_utc(cls, v: Any) -> datetime:
        return ensure_utc_datetime(v)


class PlantMetricSummary(BaseModel):
    """Summary of plant power and energy at the requested replay horizon."""
    forecast_power_mw: float = Field(..., ge=0, description="Forecasted generation power in MW")
    forecast_energy_mwh: float = Field(..., ge=0, description="Forecasted generation energy in MWh")
    physical_baseline_power_mw: float = Field(..., ge=0, description="Calculated unconstrained physical power in MW")
    physical_baseline_energy_mwh: float = Field(..., ge=0, description="Unconstrained physical expected energy in MWh")
    actual_power_mw: float = Field(..., ge=0, description="Measured actual power in MW")
    actual_energy_mwh: float = Field(..., ge=0, description="Measured actual energy in MWh")
    grid_dispatch_limit_mw: float = Field(..., ge=0, description="Current grid dispatch limit in MW")
    curtailment_active: bool = Field(False, description="Whether plant is constrained by grid curtailment")


class ReplayResponse(UtcModel):
    """
    Forensic investigation response representing the exact state of knowledge
    and forensic conclusions knowable at replay_time.
    """
    scenario_id: str = Field(..., description="Identifier of the investigated scenario")
    replay_time: datetime = Field(..., description="The time-lock replay timestamp (UTC)")
    model_version: str = Field("AUDITRA-CORE-V0.1", description="Engine version used for forensic investigation")
    plant_id: str = Field("HELIOS-1", description="Asset investigated")
    
    # Evidence state
    total_scenario_evidence_count: int = Field(..., ge=0, description="Total evidence generated across all time")
    eligible_evidence_count: int = Field(..., ge=0, description="Number of evidence records available at or before replay_time")
    
    # Metrics, Attribution & Hypotheses
    plant_metrics: PlantMetricSummary = Field(..., description="Core power and energy balances")
    loss_attribution: LossAttribution = Field(..., description="Non-overlapping shortfall accounting")
    hypotheses: List[HypothesisResult] = Field(..., description="Evaluation of the 6 competing hypotheses")
    recovery_estimate: RecoveryEstimate = Field(..., description="Preventability and recoverable energy bounds")
    eligible_evidence: Optional[List[EvidenceRecord]] = Field(
        None, description="Detailed list of evidence available at or before replay_time"
    )

    @field_validator("replay_time", mode="before")
    @classmethod
    def parse_utc(cls, v: Any) -> datetime:
        return ensure_utc_datetime(v)


class ReplayContext(UtcModel):
    """
    Structured temporal replay context produced by the replay orchestrator
    and supplied to the forensic engine.
    Ensures zero future data leakage.
    """
    scenario_id: str = Field(..., description="Target scenario identifier")
    replay_time: datetime = Field(..., description="Forensic replay perspective timestamp (UTC)")
    eligible_telemetry: List[TelemetryRecord] = Field(default_factory=list, description="Telemetry records with available_at <= replay_time")
    eligible_forecasts: List[ForecastRecord] = Field(default_factory=list, description="Forecast records with available_at <= replay_time")
    eligible_dispatches: List[DispatchRecord] = Field(default_factory=list, description="Dispatch records with available_at <= replay_time")
    eligible_evidence: List[EvidenceRecord] = Field(default_factory=list, description="Evidence records with available_at <= replay_time")
    excluded_evidence: List[EvidenceRecord] = Field(default_factory=list, description="Late-arriving evidence records where available_at > replay_time")
    data_quality_flags: List[str] = Field(default_factory=list, description="Audit flags regarding missing, delayed or suspect data")

    @field_validator("replay_time", mode="before")
    @classmethod
    def parse_utc(cls, v: Any) -> datetime:
        return ensure_utc_datetime(v)

