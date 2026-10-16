# AUDITRA API Contracts & Specification

This document defines the REST API interface for AUDITRA, implemented via FastAPI in `backend/app/main.py`.

---

## 1. Global Conventions & Standards

- **Base URL**: `http://localhost:8000`
- **Timestamp Standard**: ISO-8601 with explicit timezone (e.g. `2026-06-15T12:00:00Z`). All timestamps are validated and converted to UTC. Naive timestamps are rejected with HTTP 422.
- **Units**:
  - Power: Megawatts (`MW`)
  - Energy: Megawatt-hours (`MWh`)
  - Irradiance: Watts per square meter (`W/m²`)
  - Temperature: Degrees Celsius (`°C`)

---

## 2. Endpoints

### 2.1 System Health
`GET /api/health`

Returns application operational status and version.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "AUDITRA-Backend",
  "version": "0.1.0",
  "timestamp": "2026-10-17T00:15:00.000000Z"
}
```

---

### 2.2 Scenario Catalog
`GET /api/scenarios`

Returns the list of available synthetic demonstration scenarios for Helios-1 Solar Park.

**Response (200 OK):**
```json
[
  {
    "scenario_id": "SCENARIO-01-THERMAL-TRIP",
    "title": "Helios-1 Inverter Block 2 Overheating & Trip",
    "description": "High irradiance event causing INV-02 thermal alarm, delayed telemetry ingestion, and subsequent inverter shutdown.",
    "start_time": "2026-06-15T10:00:00Z",
    "end_time": "2026-06-15T16:00:00Z",
    "incident_category": "Equipment Derating & Failure"
  },
  {
    "scenario_id": "SCENARIO-02-GRID-CURTAILMENT-WEATHER",
    "title": "Overlapping Grid Curtailment & Cloud Transient",
    "description": "Grid operator dispatch cap active concurrently with sudden irradiance drop, demonstrating non-overlapping attribution.",
    "start_time": "2026-07-10T11:00:00Z",
    "end_time": "2026-07-10T15:00:00Z",
    "incident_category": "Compound Curtailment & Weather"
  },
  {
    "scenario_id": "SCENARIO-03-SENSOR-DRIFT",
    "title": "Primary Pyranometer Calibration Drift",
    "description": "Primary POA pyranometer degrades relative to secondary reference sensor, creating false forecast shortfall.",
    "start_time": "2026-08-05T09:00:00Z",
    "end_time": "2026-08-05T17:00:00Z",
    "incident_category": "Instrumentation & Sensor Drift"
  }
]
```

---

### 2.3 Time-Locked Forensic Replay
`POST /api/replay`

Executes a forensic investigation up to a specific historical timestamp $T$. Only telemetry and evidence records where `available_at <= T` are included.

**Request Body (`ReplayRequest`):**
```json
{
  "scenario_id": "SCENARIO-01-THERMAL-TRIP",
  "replay_time": "2026-06-15T12:15:00Z",
  "include_evidence_log": true
}
```

**Response Body (`ReplayResponse`):**
```json
{
  "scenario_id": "SCENARIO-01-THERMAL-TRIP",
  "replay_time": "2026-06-15T12:15:00Z",
  "model_version": "AUDITRA-CORE-V0.1",
  "plant_id": "HELIOS-1",
  "total_scenario_evidence_count": 48,
  "eligible_evidence_count": 22,
  "plant_metrics": {
    "forecast_power_mw": 48.0,
    "forecast_energy_mwh": 12.0,
    "physical_baseline_power_mw": 46.5,
    "physical_baseline_energy_mwh": 11.625,
    "actual_power_mw": 34.0,
    "actual_energy_mwh": 8.5,
    "grid_dispatch_limit_mw": 50.0,
    "curtailment_active": false
  },
  "loss_attribution": {
    "total_forecast_energy_mwh": 12.0,
    "total_actual_energy_mwh": 8.5,
    "total_shortfall_mwh": 3.5,
    "weather_loss_mwh": 0.375,
    "curtailment_loss_mwh": 0.0,
    "equipment_loss_mwh": 2.85,
    "other_validated_loss_mwh": 0.0,
    "unexplained_residual_mwh": 0.275,
    "breakdown": [
      {
        "category": "WEATHER_VARIANCE",
        "loss_mwh": 0.375,
        "equivalent_power_mw": 1.5,
        "percentage_of_shortfall": 10.71,
        "ruling_basis": "Forecast POA 1000 W/m² vs Validated POA 970 W/m²"
      },
      {
        "category": "EQUIPMENT_DERATING",
        "loss_mwh": 2.85,
        "equivalent_power_mw": 11.4,
        "percentage_of_shortfall": 81.43,
        "ruling_basis": "INV-02 thermal trip with confirmed cabinet alarm"
      },
      {
        "category": "UNEXPLAINED_RESIDUAL",
        "loss_mwh": 0.275,
        "equivalent_power_mw": 1.1,
        "percentage_of_shortfall": 7.86,
        "ruling_basis": "Unattributed telemetry variance"
      }
    ],
    "precedence_order": [
      "WEATHER_VARIANCE",
      "GRID_CURTAILMENT",
      "EQUIPMENT_DERATING",
      "OTHER_VALIDATED",
      "UNEXPLAINED_RESIDUAL"
    ]
  },
  "hypotheses": [
    {
      "hypothesis_id": "H1_EQUIPMENT_DERATING",
      "title": "H1: Equipment Derating & Hardware Trip",
      "status": "SUPPORTED",
      "confidence_score": 0.94,
      "ruling_criteria": "INV-02 output = 0 MW while peer blocks INV-01/03/04 generating at >11 MW with correlated high temp alarm EV-014",
      "supporting_evidence_ids": ["EV-012", "EV-014", "EV-015"],
      "contradicting_evidence_ids": [],
      "missing_evidence": [],
      "summary": "Inverter block 2 suffered an over-temperature trip at 11:58 UTC. Confirmed by SCADA alarm telemetry available at 12:02 UTC."
    },
    {
      "hypothesis_id": "H2_WEATHER_DROP",
      "title": "H2: Weather & Irradiance Drop",
      "status": "CONTRADICTED",
      "confidence_score": 0.12,
      "ruling_criteria": "POA irradiance remained at 970 W/m², which accounts for only 0.375 MWh of the 3.5 MWh shortfall.",
      "supporting_evidence_ids": ["EV-008"],
      "contradicting_evidence_ids": ["EV-009", "EV-010"],
      "missing_evidence": [],
      "summary": "Weather conditions were mostly sunny; insufficient cloud transient to explain plant-level generation drop."
    },
    {
      "hypothesis_id": "H3_GRID_CURTAILMENT",
      "title": "H3: Grid Curtailment Order",
      "status": "CONTRADICTED",
      "confidence_score": 0.0,
      "ruling_criteria": "Grid dispatch limit was 50.0 MW (unconstrained).",
      "supporting_evidence_ids": [],
      "contradicting_evidence_ids": ["EV-003"],
      "missing_evidence": [],
      "summary": "No grid operator curtailment instruction was active during this interval."
    },
    {
      "hypothesis_id": "H4_SENSOR_DRIFT",
      "title": "H4: Pyranometer Sensor Drift",
      "status": "CONTRADICTED",
      "confidence_score": 0.05,
      "ruling_criteria": "Delta between primary and secondary pyranometer was 0.8% (< 3.0% threshold).",
      "supporting_evidence_ids": [],
      "contradicting_evidence_ids": ["EV-006", "EV-007"],
      "missing_evidence": [],
      "summary": "Primary and reference irradiance sensors are in close agreement."
    },
    {
      "hypothesis_id": "H5_FORECAST_BIAS",
      "title": "H5: Persistent Forecast Model Bias",
      "status": "INCONCLUSIVE",
      "confidence_score": null,
      "ruling_criteria": "Requires multi-day normalized baseline under clear-sky conditions.",
      "supporting_evidence_ids": [],
      "contradicting_evidence_ids": [],
      "missing_evidence": ["7-day rolling forecast validation telemetry"],
      "summary": "Insufficient historical depth in this interval to isolate systematic day-ahead forecast model bias."
    },
    {
      "hypothesis_id": "H6_UNEXPLAINED_RESIDUAL",
      "title": "H6: Unexplained Residual Shortfall",
      "status": "SUPPORTED",
      "confidence_score": 1.0,
      "ruling_criteria": "Unattributed shortfall = 0.275 MWh (7.86% of total shortfall).",
      "supporting_evidence_ids": ["EV-RESIDUAL-01"],
      "contradicting_evidence_ids": [],
      "missing_evidence": [],
      "summary": "7.86% of the shortfall remains unexplained after accounting for validated weather and equipment factors."
    }
  ],
  "recovery_estimate": {
    "observed_loss_mwh": 2.85,
    "detectable_loss_mwh": 2.85,
    "actionable_loss_mwh": 2.10,
    "preventable_loss_mwh": 1.65,
    "recoverable_energy_mwh_min": 1.20,
    "recoverable_energy_mwh_max": 1.65,
    "limiting_factors": [
      "15-minute SCADA polling interval",
      "Control room dispatch acknowledgment latency (5 min)",
      "Inverter thermal cool-down thermal inertia (25 min)"
    ],
    "assumptions": [
      "Operator resets inverter within 10 minutes of alarm arrival",
      "No physical component replacement required (soft thermal trip)"
    ]
  }
}
```
