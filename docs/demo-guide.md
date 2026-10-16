# AUDITRA Demonstration & Judge Walkthrough Guide

This guide details the reproducible, step-by-step forensic investigation demonstration for FIX PS3 hackathon judges.

---

## 1. Demonstration Scenario: `SCENARIO-01-THERMAL-TRIP`
**Helios-1 Solar Park Inverter Block 2 Overheating & Trip**

- **Asset**: Helios-1 (50.0 MW AC nameplate, 4x 12.5 MW inverter blocks)
- **Time Horizon**: June 15, 2026, 11:00 UTC to 14:00 UTC
- **Incident Summary**: At 11:55 UTC, `INV-02` experiences an internal cooling fan malfunction during peak solar irradiance ($970\text{ W/m}^2$). The inverter cabinet temperature spikes above $70^\circ\text{C}$, triggering an automatic over-temperature hardware shutdown. Due to a 15-minute SCADA polling delay, telemetry arrives at 12:10 UTC.

---

## 2. Nine-Step Forensic Investigation Walkthrough

### Step 1: Select Incident Scenario
- Launch the AUDITRA dashboard at `http://localhost:5173`.
- In the top scenario ribbon, select **`SCENARIO-01-THERMAL-TRIP`**.
- Notice the plant parameters: Helios-1, 50.0 MW rated capacity, 15-minute telemetry intervals.

### Step 2: Establish the Forensic Discrepancy
- Observe the generation shortfall: Day-ahead forecast predicted **48.0 MW**, but measured export dropped to **34.0 MW** (shortfall of 14.0 MW / 3.5 MWh in interval).
- State the core forensic question: *"Was this drop predictable, controllable, or bad luck?"*

### Step 3: Set Replay Perspective to $T_1 = 12:00\text{ UTC}$ (Hindsight-Free)
- Scrub the flight-recorder timeline to **12:00 UTC**.
- **What is known**: Actual power has dropped to 34 MW. POA irradiance remains high ($970\text{ W/m}^2$).
- **What is NOT known**: The SCADA trip alarm has not arrived yet due to telemetry transmission delay (`available_at = 12:10 UTC`).
- **Hypothesis Status at 12:00 UTC**:
  - `H2_WEATHER_DROP`: **CONTRADICTED** (irradiance is high).
  - `H1_EQUIPMENT_DERATING`: **INSUFFICIENT_DATA** (output drop observed, but root-cause telemetry not yet available).
  - `H6_UNEXPLAINED_RESIDUAL`: **SUPPORTED** (large unexplained gap).

### Step 4: Advance Replay Timeline to $T_2 = 12:15\text{ UTC}$ (Evidence Ingestion)
- Advance the scrubber to **12:15 UTC**.
- The time-locked filter now admits record `EV-014` (`available_at = 12:10 UTC`): *"INV-02 cabinet temperature 72°C - OVER_TEMP_TRIP"*.
- **Forensic Engine updates in real time**:
  - `H1_EQUIPMENT_DERATING` transitions to **SUPPORTED** (confidence calibrated at 94%).
  - Peer blocks (`INV-01`, `INV-03`, `INV-04`) continue generating at $>11.2\text{ MW}$ each under identical POA irradiance, isolating the fault to `INV-02`.

### Step 5: Evaluate the Six Competing Hypotheses
Review the matrix on the forensic console:
1. **H1 (Equipment Derating)**: **SUPPORTED** (correlated with INV-02 alarm and peer divergence).
2. **H2 (Weather Drop)**: **CONTRADICTED** (POA irradiance accounts for only 0.375 MWh of shortfall).
3. **H3 (Grid Curtailment)**: **CONTRADICTED** (dispatch limit 50.0 MW; unconstrained).
4. **H4 (Sensor Drift)**: **CONTRADICTED** (primary vs reference pyranometer within 0.8%).
5. **H5 (Forecast Bias)**: **INCONCLUSIVE** (insufficient clear-sky multi-day baseline).
6. **H6 (Unexplained Residual)**: **SUPPORTED** (explicit 0.275 MWh residual reported honestly).

### Step 6: Review Non-Overlapping Loss Waterfall
- Total Shortfall: **3.50 MWh**
- $\Delta E_{\text{weather}}$: **0.375 MWh** (minor irradiance variance below 1000 W/m² STC)
- $\Delta E_{\text{curtailment}}$: **0.00 MWh** (no grid curtailment)
- $\Delta E_{\text{equipment}}$: **2.85 MWh** (INV-02 shutdown)
- $\Delta E_{\text{residual}}$: **0.275 MWh** (7.86% unmodeled variance)
- **Sum reconciles exactly to 3.50 MWh without double-counting**.

### Step 7: Inspect Evidence Provenance & Audit Trail
- Click on `EV-014` in the evidence list.
- Verify timestamps: `event_time = 11:55 UTC`, `available_at = 12:10 UTC`.
- Note provenance: `INVERTER_SCADA`, Quality: `VALIDATED`.

### Step 8: Assess Preventability & Recoverable Energy Range
- Explain to judges: *"Even though 2.85 MWh was lost to equipment derating, could it all have been recovered?"*
- Walk through the operational counterfactual:
  - Detection lag: 15 minutes.
  - Operator acknowledgment latency: 5 minutes.
  - Inverter cool-down thermal inertia: 25 minutes.
- **Recoverable Energy**: **[1.20 MWh - 1.65 MWh]**.
- Shows mature product thinking: AUDITRA does not make inflated, unrealistic recovery claims.

### Step 9: Final Executive Recommendation
- Summarize the final forensic report:
  - Root cause: Localized thermal trip of Inverter Block 2.
  - Uncontrollable loss: 0.375 MWh (weather).
  - Controllable / Actionable loss: 1.20 - 1.65 MWh with rapid thermal reset.
  - Residual uncertainty: 0.275 MWh.
