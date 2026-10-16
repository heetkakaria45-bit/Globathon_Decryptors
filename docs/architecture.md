# AUDITRA System Architecture

AUDITRA is an industrial forensic intelligence engine designed to investigate generation shortfalls at utility-scale photovoltaic plants (Helios-1 reference asset).

---

## 1. High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph DataLayer["Data & Telemetry Layer (Amulya Dongre)"]
        SC[Scenario Generator] --> RAW[Raw Telemetry Store]
        RAW --> INGEST[Telemetry Ingestion & Quality Validator]
        INGEST --> EV_LOG[Time-Stamped Evidence Log]
    end

    subgraph ReplayLayer["Time-Locked Replay Orchestrator (Heet Kakaria)"]
        REQ[ReplayRequest: scenario_id, replay_time T] --> FILTER{Temporal Filter\navailable_at <= T}
        EV_LOG --> FILTER
        FILTER --> ELIGIBLE[Eligible Historical Evidence Set]
    end

    subgraph EngineLayer["Domain Science Engine (Atharva Hoge)"]
        ELIGIBLE --> PHYS[Physical Baseline Engine\nP_phys = min(P_cap, ...)]
        PHYS --> LOSS[Sequential Non-Overlapping\nLoss Waterfall]
        LOSS --> HYP[Evidence-Tested\n6 Hypotheses Matrix]
        HYP --> REC[Preventability & Bounded\nRecovery Estimator]
    end

    subgraph APILayer["FastAPI Interface (Amulya Dongre)"]
        REC --> RESP[ReplayResponse JSON]
        LOSS --> RESP
        HYP --> RESP
    end

    subgraph FrontendLayer["Control-Room Console (Vedant Goyal)"]
        RESP --> DASH[React 18 + Vite Dashboard]
        DASH --> TIMELINE[Flight-Recorder Timeline Scrubber]
        DASH --> WATERFALL[Recharts Loss Waterfall]
        DASH --> MATRIX[Hypothesis Ruling Board]
        DASH --> PROVENANCE[Evidence Provenance Inspector]
    end
```

---

## 2. Core Architectural Layers

### Layer 1: Data & Synthetic Scenario Ingestion (`backend/app/data/`)
- **Owner**: Amulya Dongre
- **Responsibilities**:
  - Ingests 15-minute interval records for inverter blocks `INV-01` through `INV-04`.
  - Simulates realistic operational anomalies: delayed SCADA polling, primary sensor calibration drift, inverter thermal alarms, and transmission curtailment orders.
  - Generates immutable `event_time` and `available_at` timestamps for every data point.

### Layer 2: Time-Locked Forensic Replay (`backend/app/replay/`)
- **Owner**: Heet Kakaria (Tech Lead)
- **Responsibilities**:
  - Enforces the historical time-lock boundary: for a replay instant $T$, evidence is admitted **if and only if** `available_at <= T`.
  - Strictly prevents future-arriving information (e.g. maintenance work logs logged 3 hours after a fault) from leaking into early replay views.
  - Normalizes all incoming timestamps to UTC.

### Layer 3: Domain Science & Loss Attribution Engine (`backend/app/engine/`)
- **Owner**: Atharva Hoge
- **Responsibilities**:
  - **Physical Baseline**: Computes clean unconstrained expected generation using standard STC temperature coefficients ($\gamma = -0.004/^\circ\text{C}$) and inverter clipping ($12.5\text{ MW}$ per block).
  - **Sequential Attribution Waterfall**: Allocates forecast shortfalls into mutually exclusive categories (Weather $\rightarrow$ Curtailment $\rightarrow$ Equipment $\rightarrow$ Other $\rightarrow$ Unexplained Residual).
  - **Hypothesis Evaluation**: Evaluates H1 to H6 against supporting, contradicting, and missing evidence.
  - **Recoverability Bounding**: Models detection lag, operator reaction time, and thermal cooldown to compute realistic $[E_{\text{min}}, E_{\text{max}}]$ recoverable energy bounds.

### Layer 4: Forensic Presentation & Control Console (`frontend/`)
- **Owner**: Vedant Goyal
- **Responsibilities**:
  - Provides a dark industrial control-room aesthetic.
  - Renders time-series generation profiles, flight-recorder scrubbing timeline, loss waterfall breakdown, hypothesis comparison matrix, and evidence provenance audit trail.

---

## 3. Key Design Decisions

1. **Deterministic Local Execution**:
   - No external AI inference APIs (e.g., OpenAI, Claude) are used in core causal reasoning. All forensic rules are deterministic, inspectable, and reproducible.
2. **Explicit Uncertainty & Incomplete Information**:
   - The platform never forces unexplained shortfall to zero. If sensor data is suspect or missing, the residual is reported honestly as `UNEXPLAINED_RESIDUAL` or hypothesis status `INSUFFICIENT_DATA`.
3. **Decoupled Contracts**:
   - Pydantic models in `backend/app/schemas.py` are the single source of truth. TypeScript types in `frontend/src/types/schemas.ts` are strictly synchronized to prevent frontend-backend integration friction.
