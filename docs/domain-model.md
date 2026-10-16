# AUDITRA Domain Model & Mathematical Specification

This document defines the solar photovoltaic engineering principles, baseline physics, non-overlapping loss accounting methodology, and forensic hypothesis criteria used in AUDITRA.

---

## 1. Asset Specification: Helios-1 Solar Park

Helios-1 is a utility-scale grid-tied solar photovoltaic generating asset configured as follows:

- **Nameplate AC Capacity ($P_{\text{cap}}$)**: 50.0 MW AC
- **Inverter Architecture**: 4 identical central inverter blocks:
  - `INV-01`: 12.5 MW AC
  - `INV-02`: 12.5 MW AC
  - `INV-03`: 12.5 MW AC
  - `INV-04`: 12.5 MW AC
- **Telemetry Resolution**: 15 minutes ($\Delta t = 0.25\text{ hours}$)
- **Telemetry Semantics**: Interval-average power ($P_{\text{avg}}$) in MW.
- **Energy Conversion**:
  $$E_{\text{interval}} = P_{\text{avg}} \times 0.25\quad [\text{MWh}]$$

---

## 2. Physical Generation Baseline Model

To evaluate whether underperformance was caused by external atmospheric conditions or plant equipment, AUDITRA calculates the **unconstrained physical expected power** for each inverter block $i$:

$$P_{\text{phys},i} = \min\left(P_{\text{cap},i},\; \max\left(0,\; P_{\text{cap},i} \times \left(\frac{G_{\text{clean},i}}{G_{\text{STC}}}\right) \times \left[1 + \gamma \times (T_{\text{mod},i} - T_{\text{STC}})\right]\right)\right)$$

### Parameter Definitions:
- $P_{\text{cap},i} = 12.5\text{ MW}$: Nameplate inverter AC capacity.
- $G_{\text{clean},i}$: Validated plane-of-array (POA) irradiance in $\text{W/m}^2$.
- $G_{\text{STC}} = 1000\text{ W/m}^2$: Standard Test Condition reference irradiance.
- $T_{\text{mod},i}$: Measured module backsheet temperature in degrees Celsius ($^\circ\text{C}$).
- $T_{\text{STC}} = 25^\circ\text{C}$: Standard Test Condition reference module temperature.
- $\gamma = -0.004\text{ / }^\circ\text{C}$ ($-0.4\%\text{ / }^\circ\text{C}$): Module power temperature coefficient.

### Physical Invariants & Constraints:
1. **Capacity Clamping**: Inverter AC output cannot exceed rated capacity ($12.5\text{ MW}$ per block, $50.0\text{ MW}$ plant aggregate). Even under cloud-edge irradiance spikes ($>1200\text{ W/m}^2$), output is clipped at $P_{\text{cap}}$.
2. **Non-Negativity**: Inverter AC power cannot be negative ($P_{\text{phys}} \ge 0$). At night ($G = 0$), $P_{\text{phys}} = 0$.
3. **Sensor Quality**: Missing or degraded irradiance data is flagged as `SUSPECT` or `MISSING`. It is **never silently coerced to zero**, which would falsely mask equipment losses as night/clouds.
4. **Model Limitations**: This model represents an operational baseline. It does not model spectral mismatch, complex partial shading geometry, or DC wiring ohmic degradation.

---

## 3. Non-Overlapping Loss Attribution Waterfall

When measured generation falls short of day-ahead forecast ($P_{\text{actual}} < P_{\text{forecast}}$), the total energy shortfall must be reconciled without double-counting:

$$\text{Total Shortfall [MWh]} = \max\left(0,\; E_{\text{forecast}} - E_{\text{actual}}\right)$$

### Sequential Attribution Precedence Convention:

```
[Day-Ahead Forecast Energy]
           │
           ▼
[Step 1: Weather Variance] ──► Shortfall from lower-than-forecast irradiance
           │
           ▼
[Step 2: Grid Curtailment] ──► Shortfall from active transmission dispatch cap
           │
           ▼
[Step 3: Equipment Derate] ──► Shortfall from inverter trips, thermal limits, or hardware faults
           │
           ▼
[Step 4: Other Validated]  ──► Confirmed external events (substation maintenance, etc.)
           │
           ▼
[Step 5: Unexplained Residual] ──► Explicit remaining unexplained variance
```

### Mathematical Definitions:

1. **Weather Variance Loss ($\Delta E_{\text{weather}}$)**:
   $$\Delta E_{\text{weather}} = \max\left(0,\; E_{\text{forecast}} - E_{\text{phys}}\right)$$
   Bounded by: $\min(\Delta E_{\text{weather}}, \text{Total Shortfall})$.

2. **Grid Curtailment Loss ($\Delta E_{\text{curtailment}}$)**:
   If grid dispatch limit $P_{\text{dispatch}} < P_{\text{phys}}$:
   $$\Delta E_{\text{curtailment}} = \min\left(E_{\text{phys}} - E_{\text{dispatch}},\; \text{Remaining Shortfall}\right)$$
   Else: $\Delta E_{\text{curtailment}} = 0$.

3. **Equipment Derating Loss ($\Delta E_{\text{equipment}}$)**:
   Expected available output given weather and curtailment is $E_{\text{avail}} = \min(E_{\text{phys}}, E_{\text{dispatch}})$.
   $$\Delta E_{\text{equipment}} = \min\left(\max(0, E_{\text{avail}} - E_{\text{actual}}),\; \text{Remaining Shortfall}\right)$$
   Supported by inverter availability telemetry and thermal/electrical alarm evidence.

4. **Other Validated Losses ($\Delta E_{\text{other}}$)**:
   Attributed to external logged operational disruptions.

5. **Unexplained Residual ($\Delta E_{\text{residual}}$)**:
   $$\Delta E_{\text{residual}} = \text{Total Shortfall} - \left(\Delta E_{\text{weather}} + \Delta E_{\text{curtailment}} + \Delta E_{\text{equipment}} + \Delta E_{\text{other}}\right)$$

### Invariants:
- $\Delta E_k \ge 0$ for all categories $k$.
- $\sum_k \Delta E_k = \text{Total Shortfall}$ within a numerical tolerance of $10^{-3}\text{ MWh}$.
- Precedence Limitation Note: Sequential allocation is an accounting convention. It assumes weather effects precede grid actions, which precede hardware behavior. AUDITRA explicitly notes this distinction.

### 3.1 Compounding Interaction: Partial Inverter Derating Under Active Grid Curtailment

A critical domain edge case occurs when an inverter suffers a thermal or electrical derating **concurrently** with an active grid curtailment order.

#### Engineering Decision & Precedence Convention:
AUDITRA adopts the **"Dispatch Headroom First" (Curtailment Priority over Counterfactual Derating)** convention:

1. **Physical Potential Baseline ($E_{\text{phys}}$)**: Unconstrained generation permitted by clean POA irradiance and module temperature.
2. **Allowable Injection ($E_{\text{dispatch}}$)**: Maximum allowable energy the plant could export under the active transmission constraint:
   $$E_{\text{allowed}} = \min(E_{\text{phys}}, E_{\text{dispatch}})$$
3. **Curtailment Allocation ($\Delta E_{\text{curtailment}}$)**:
   The portion of shortfall between physical potential and the dispatch limit, bounded by the plant's actual delivery capability:
   $$\Delta E_{\text{curtailment}} = \max\left(0,\; E_{\text{phys}} - \max(E_{\text{dispatch}}, E_{\text{actual}})\right)$$
   - *Case A (Absorbed Derate)*: If one block derates (e.g. lost 5 MW), but remaining healthy blocks generate enough to reach $E_{\text{dispatch}}$ ($E_{\text{actual}} = E_{\text{dispatch}}$), the equipment derating caused **zero lost export**. All shortfall relative to $E_{\text{phys}}$ is allocated to **Curtailment**.
   - *Case B (Penetrating Derate)*: If the derating prevents the plant from reaching the dispatch cap ($E_{\text{actual}} < E_{\text{dispatch}}$), the curtailment loss is capped at $E_{\text{phys}} - E_{\text{dispatch}}$, and the deficit below the cap is allocated to **Equipment Derating**.
4. **Equipment Loss Allocation ($\Delta E_{\text{equipment}}$)**:
   $$\Delta E_{\text{equipment}} = \max\left(0,\; E_{\text{allowed}} - E_{\text{actual}}\right)$$
   Only the shortfall that **actually caused plant generation to drop below allowable grid export** is booked as equipment loss.

#### Numerical Case Comparison:
Assume $E_{\text{forecast}} = 12.0\text{ MWh}$, $E_{\text{phys}} = 12.0\text{ MWh}$ (no weather loss), and Grid Dispatch Cap $= 8.0\text{ MWh}$ ($\Delta E_{\text{curt, potential}} = 4.0\text{ MWh}$):

| Scenario | $E_{\text{actual}}$ | Equipment Fault | $\Delta E_{\text{weather}}$ | $\Delta E_{\text{curtailment}}$ | $\Delta E_{\text{equipment}}$ | $\Delta E_{\text{residual}}$ | Total Shortfall | Physical Interpretation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Normal Curtailment** | 8.0 MWh | None | 0.0 | 4.0 MWh | 0.0 | 0.0 | 4.0 MWh | Plant tracks grid setpoint cleanly. |
| **Absorbed Derate** | 8.0 MWh | INV-02 at 50% | 0.0 | 4.0 MWh | 0.0 | 0.0 | 4.0 MWh | Peer inverters absorb derating; export unaffected. |
| **Penetrating Derate** | 6.5 MWh | INV-02 trip | 0.0 | 4.0 MWh | 1.5 MWh | 0.0 | 5.5 MWh | Grid blocked 4.0 MWh; trip caused 1.5 MWh drop below cap. |

This convention aligns directly with utility Power Purchase Agreements (PPAs) and prevents unfair penalization of asset operators when generation was curtailed by grid operators anyway.

---

## 4. The Six Competing Hypotheses

| Hypothesis | Evaluation Target | Supporting Evidence Signature | Contradicting Signature |
| :--- | :--- | :--- | :--- |
| **H1: Equipment Derating** | Inverter hardware fault, thermal throttling, or component trip | $\text{INV}_i$ output drops while peer blocks generate normally under identical POA; internal temp $>65^\circ\text{C}$; SCADA trip alarms | All 4 blocks drop identically with no alarms; inverter internal temp normal |
| **H2: Weather Drop** | Atmospheric cloud cover or irradiance shortfall | POA pyranometers confirm irradiance drop; physical expected power matches measured power | POA pyranometer reads $>950\text{ W/m}^2$ while actual generation is degraded |
| **H3: Grid Curtailment** | Transmission system operator export limit | Active dispatch constraint flag; plant export tracks dispatch cap with low standard deviation | Dispatch limit $>50\text{ MW}$; no curtailment flag in telemetry |
| **H4: Sensor Drift** | Pyranometer degradation or calibration error | Primary POA sensor differs from independent reference pyranometer by $>3.0\%$ | Primary and reference sensors agree within $\pm 1.0\%$ |
| **H5: Forecast Bias** | Systematic day-ahead forecasting algorithm bias | Persistent, multi-day negative bias under verified clear-sky conditions | Error occurs only during localized transient events |
| **H6: Unexplained Residual** | Remaining shortfall without validated physical evidence | $\Delta E_{\text{residual}} > 0.05 \times \text{Total Shortfall}$ | Complete reconciliation with zero residual |

---

## 5. Preventability and Recoverable Energy Modeling

Observed generation loss is **not automatically preventable**. AUDITRA models the operational response pipeline:

```
Physical Event Occurs (event_time)
           │
           │  Detection Delay (SCADA poll interval: 0 - 15 min)
           ▼
Information Available in Control Room (available_at)
           │
           │  Diagnosis & Acknowledgment Delay (5 - 10 min)
           ▼
Actionable Response Initiated
           │
           │  Intervention Execution (Remote reset or dispatch: 5 - 20 min)
           ▼
Plant Output Recovered
```

### Recoverable Energy Bounds:
- **Observed Loss ($E_{\text{obs}}$)**: Total lost MWh.
- **Detectable Loss ($E_{\text{det}}$)**: Loss occurring after telemetry threshold crossed.
- **Actionable Loss ($E_{\text{act}}$)**: Loss occurring after information reaches operator.
- **Recoverable Energy Range $[E_{\text{rec, min}}, E_{\text{rec, max}}]$**:
  $$E_{\text{rec, max}} = E_{\text{act}} - \left(P_{\text{derate}} \times \Delta t_{\text{min\_response}}\right)$$
  $$E_{\text{rec, min}} = \max\left(0,\; E_{\text{act}} - \left(P_{\text{derate}} \times \Delta t_{\text{conservative\_response}}\right)\right)$$
- Always constrained by remaining daylight generation window and inverter nameplate capacity.
