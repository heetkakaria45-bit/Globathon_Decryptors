# AUDITRA Acceptance Tests Specification

This document defines the formal acceptance criteria and test conditions required to certify AUDITRA for competition judging.

---

## 1. Domain Physics & Mathematics Acceptance Criteria

| Test ID | Condition Tested | Expected Behavior | Verification Status |
| :--- | :--- | :--- | :--- |
| **DOM-01** | Inverter Capacity Clamping | Calculated physical power $P_{\text{phys}}$ for any block cannot exceed $12.5\text{ MW}$ under any irradiance condition ($>1200\text{ W/m}^2$). | **PASSED** (`test_engine.py`) |
| **DOM-02** | Non-Negative Power | $P_{\text{phys}} \ge 0.0\text{ MW}$ even at night ($G = 0$) or extreme cold temperatures. | **PASSED** (`test_engine.py`) |
| **DOM-03** | Temperature Derating | Module temperatures above $25^\circ\text{C}$ derate power according to $\gamma = -0.004\text{ / }^\circ\text{C}$ ($10\%$ loss at $50^\circ\text{C}$). | **PASSED** (`test_engine.py`) |
| **DOM-04** | Missing Sensor Handling | Irradiance flagged as `MISSING` or `SUSPECT` raises an audit flag; never silently coerced to $0.0\text{ W/m}^2$. | **PASSED** (`test_schemas.py`) |
| **DOM-05** | Energy Conversion | Interval energy adheres to $E_{\text{MWh}} = P_{\text{MW}} \times 0.25$ over 15-minute intervals. | **PASSED** (`test_engine.py`) |
| **DOM-06** | Loss Accounting Identity | $\text{Shortfall} = \text{Weather} + \text{Curtailment} + \text{Equipment} + \text{Other} + \text{Residual}$ reconciles within $10^{-3}\text{ MWh}$. | **PASSED** (`test_engine.py`) |
| **DOM-07** | Zero Double-Counting | Overlapping irradiance dips and inverter trips do not duplicate loss allocation. | **PASSED** (`test_engine.py`) |

---

## 2. Time-Locked Replay Acceptance Criteria

| Test ID | Condition Tested | Expected Behavior | Verification Status |
| :--- | :--- | :--- | :--- |
| **RPL-01** | Exact Availability Match | Evidence where `available_at == replay_time` is eligible for the investigation. | **PASSED** (`test_replay.py`) |
| **RPL-02** | Future Evidence Exclusion | Evidence where `available_at > replay_time` (even by 1 second) is quarantined into `excluded_evidence`. | **PASSED** (`test_replay.py`) |
| **RPL-03** | Late-Reported Physical Event | An event occurring at $T-30\text{m}$ but available at $T+15\text{m}$ is strictly excluded at replay time $T$. | **PASSED** (`test_replay.py`) |
| **RPL-04** | Timezone Invariance | $12:00\text{ UTC}$ and $17:30\text{ IST}$ produce identical eligible evidence sets and identical conclusions. | **PASSED** (`test_replay.py`) |
| **RPL-05** | Replay Determinism | Multiple replay queries with identical scenario and timestamp inputs return identical results. | **PASSED** (`test_replay.py`) |
| **RPL-06** | Forecast Revisions | Later forecast revisions available after $T$ are excluded in favor of earlier active revisions. | **PASSED** (`test_replay.py`) |
| **RPL-07** | Naive Timestamp Rejection | Request or telemetry with naive datetime is rejected with HTTP 422 / ValidationError. | **PASSED** (`test_replay.py`) |

---

## 3. Forensic Hypotheses Acceptance Criteria

| Test ID | Condition Tested | Expected Behavior | Verification Status |
| :--- | :--- | :--- | :--- |
| **HYP-01** | Evidence Provenance | Every hypothesis ruling references specific supporting and contradicting evidence IDs. | **SPECIFIED** (`schemas.py`) |
| **HYP-02** | Insufficient Evidence | Hypotheses with missing prerequisite sensors must be classified as `INSUFFICIENT_DATA`, not fabricated conclusions. | **SPECIFIED** (`schemas.py`) |
| **HYP-03** | Explicit Residual | If shortfall cannot be attributed to validated physical causes, `H6_UNEXPLAINED_RESIDUAL` is marked `SUPPORTED`. | **SPECIFIED** (`schemas.py`) |

---

## 4. Preventability & Recoverable Energy Acceptance Criteria

| Test ID | Condition Tested | Expected Behavior | Verification Status |
| :--- | :--- | :--- | :--- |
| **REC-01** | Bounded Recovery | Recoverable energy range satisfies $0 \le E_{\text{rec, min}} \le E_{\text{rec, max}} \le E_{\text{observed}}$. | **PASSED** (`test_engine.py`) |
| **REC-02** | Response Lag Modeling | Recoverable energy excludes detection delay, operator acknowledgment time, and hardware cooldown inertia. | **SPECIFIED** (`domain-model.md`) |
| **REC-03** | Counterfactual Assumptions | Recovery estimates explicitly report operational assumptions and limiting factors. | **PASSED** (`test_engine.py`) |

---

## 5. System Integration & Performance Criteria

| Test ID | Condition Tested | Expected Behavior | Verification Status |
| :--- | :--- | :--- | :--- |
| **INT-01** | Health Check Endpoint | `GET /api/health` returns status `healthy` and service identifier. | **PASSED** (`test_api.py`) |
| **INT-02** | Scenario Catalog | `GET /api/scenarios` returns available synthetic scenarios. | **PASSED** (`test_api.py`) |
| **INT-03** | Schema Serialization | All API payloads serialize to clean JSON with ISO-8601 UTC datetimes and no untyped dicts. | **PASSED** (`test_api.py`) |
| **INT-04** | Local-First Execution | Complete application runs locally without external internet access or external AI cloud services. | **PASSED** (Local pytest & Vite) |
