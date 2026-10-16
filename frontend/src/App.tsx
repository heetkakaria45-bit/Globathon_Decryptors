import React, { useEffect, useState } from 'react';
import { 
  Activity, 
  Clock, 
  Cpu, 
  Sliders, 
  FileText, 
  CheckCircle2, 
  AlertCircle,
  Layers
} from 'lucide-react';
import { fetchHealth, fetchScenarios } from './services/api';
import { ScenarioSummary } from './types/schemas';

export const App: React.FC = () => {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('SCENARIO-01-THERMAL-TRIP');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        const [healthRes, scenariosRes] = await Promise.all([
          fetchHealth().catch(() => ({ status: 'offline', version: '0.1.0' })),
          fetchScenarios().catch(() => [
            {
              scenario_id: 'SCENARIO-01-THERMAL-TRIP',
              title: 'Helios-1 Inverter Block 2 Overheating & Trip',
              description: 'Thermal alarm, delayed telemetry ingestion, and subsequent inverter shutdown.',
              start_time: '2026-06-15T10:00:00Z',
              end_time: '2026-06-15T16:00:00Z',
              incident_category: 'Equipment Derating & Failure'
            },
            {
              scenario_id: 'SCENARIO-02-GRID-CURTAILMENT-WEATHER',
              title: 'Overlapping Grid Curtailment & Cloud Transient',
              description: 'Grid dispatch cap active concurrently with sudden irradiance drop.',
              start_time: '2026-07-10T11:00:00Z',
              end_time: '2026-07-10T15:00:00Z',
              incident_category: 'Compound Curtailment & Weather'
            },
            {
              scenario_id: 'SCENARIO-03-SENSOR-DRIFT',
              title: 'Primary Pyranometer Calibration Drift',
              description: 'Primary POA sensor degrades relative to secondary reference pyranometer.',
              start_time: '2026-08-05T09:00:00Z',
              end_time: '2026-08-05T17:00:00Z',
              incident_category: 'Instrumentation & Sensor Drift'
            }
          ])
        ]);
        setHealth(healthRes);
        setScenarios(scenariosRes);
      } catch (err: any) {
        setError(err.message || 'Failed to initialize console');
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  const hypotheses = [
    { id: 'H1', name: 'Equipment Derating', desc: 'Inverter-block divergence, thermal telemetry, and alarm flags' },
    { id: 'H2', name: 'Weather Drop', desc: 'Cross-sensor irradiance reduction and physical baseline tracking' },
    { id: 'H3', name: 'Grid Curtailment', desc: 'Transmission operator dispatch caps and curtailment telemetry' },
    { id: 'H4', name: 'Sensor Drift', desc: 'Disagreement between primary and reference pyranometers' },
    { id: 'H5', name: 'Forecast Bias', desc: 'Systematic forecast error under verified standard conditions' },
    { id: 'H6', name: 'Unexplained Residual', desc: 'Remaining shortfall after non-overlapping attribution' }
  ];

  return (
    <div className="min-h-screen bg-[#0b0f14] text-slate-200 flex flex-col font-sans">
      {/* Top Industrial Navigation Header */}
      <header className="border-b border-[#1e2c3e] bg-[#111822]/90 backdrop-blur px-6 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_#00d2ff]" />
            <span className="font-mono text-xl tracking-wider font-bold text-white">AUDITRA</span>
          </div>
          <span className="text-xs px-2.5 py-1 rounded bg-[#1e2c3e] border border-[#2b3f58] text-cyan-300 font-mono">
            FIX PS3 // FORENSIC CORE
          </span>
          <span className="text-xs text-slate-400 hidden md:inline">
            Helios-1 Solar Park (50.0 MW AC / 4x 12.5 MW Blocks)
          </span>
        </div>

        <div className="flex items-center space-x-4 text-xs font-mono">
          {error && (
            <span className="text-rose-400 bg-rose-950/60 border border-rose-800 px-2.5 py-1 rounded">
              {error}
            </span>
          )}
          <div className="flex items-center space-x-2 bg-[#172230] px-3 py-1.5 rounded border border-[#2b3f58]">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">ENGINE:</span>
            <span className={health?.status === 'healthy' ? 'text-emerald-400' : 'text-amber-400'}>
              {loading ? 'CONNECTING...' : health?.status ? health.status.toUpperCase() : 'OFFLINE'}
            </span>
          </div>
          <div className="bg-[#172230] px-3 py-1.5 rounded border border-[#2b3f58] text-slate-300">
            REPLAY TIME: <span className="text-cyan-300">UTC LOCKED</span>
          </div>
        </div>
      </header>

      {/* Main Forensic Console Body */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        
        {/* Scenario Selection & Mission Ribbon */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-[#111822] border border-[#1e2c3e] rounded-lg p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyan-400" /> Incident Investigation Scenario
              </h2>
              <span className="text-xs text-cyan-400 font-mono">Deterministic Synthetic Replay</span>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {scenarios.map((sc) => (
                <button
                  key={sc.scenario_id}
                  onClick={() => setSelectedScenarioId(sc.scenario_id)}
                  className={`text-left p-3 rounded border transition-all text-xs ${
                    selectedScenarioId === sc.scenario_id
                      ? 'border-cyan-500 bg-[#172230] text-white shadow-[0_0_15px_rgba(0,210,255,0.15)]'
                      : 'border-[#1e2c3e] bg-[#0b0f14]/60 text-slate-400 hover:border-[#2b3f58] hover:text-slate-300'
                  }`}
                >
                  <div className="font-mono text-[11px] text-cyan-400/80 mb-1">{sc.scenario_id}</div>
                  <div className="font-medium line-clamp-1 text-slate-200">{sc.title}</div>
                  <div className="mt-2 text-[10px] text-slate-500 font-mono">
                    {sc.incident_category}
                  </div>
                </button>
              ))}
            </div>

            <div className="mt-4 pt-3 border-t border-[#1e2c3e] text-xs text-slate-400 flex items-center justify-between">
              <span>Selected Target: <strong className="text-slate-200 font-mono">{selectedScenarioId}</strong></span>
              <span className="font-mono text-cyan-400">15-min interval duration (0.25h)</span>
            </div>
          </div>

          {/* Core Forensic Question */}
          <div className="bg-[#111822] border border-[#1e2c3e] rounded-lg p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono text-amber-400 mb-2">
                <AlertCircle className="w-4 h-4" /> CORE FORENSIC QUESTION
              </div>
              <p className="text-sm text-slate-200 italic font-serif">
                "The forecast was wrong. Was that predictable, controllable, or just bad luck?"
              </p>
              <p className="mt-3 text-xs text-slate-400 leading-relaxed">
                AUDITRA answers this through time-locked forensic replay, unconstrained physical baselines, sequential non-overlapping loss accounting, and bounded recoverable energy.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#1e2c3e] flex items-center justify-between text-xs font-mono text-slate-400">
              <span>PLANT: HELIOS-1</span>
              <span className="text-cyan-400">P_CAP: 50.0 MW</span>
            </div>
          </div>
        </div>

        {/* 6 Competing Hypotheses Matrix */}
        <div className="bg-[#111822] border border-[#1e2c3e] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" /> Six Competing Forensic Hypotheses
            </h2>
            <span className="text-xs text-slate-500 font-mono">Evidence-Tested Evaluation Matrix</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {hypotheses.map((hyp) => (
              <div 
                key={hyp.id} 
                className="p-4 rounded border border-[#1e2c3e] bg-[#0b0f14]/50 hover:border-[#2b3f58] transition-all"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-[#172230] text-cyan-400 border border-[#2b3f58]">
                    {hyp.id}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    AWAITING REPLAY
                  </span>
                </div>
                <h3 className="text-sm font-medium text-slate-200">{hyp.name}</h3>
                <p className="mt-1 text-xs text-slate-400 leading-normal">{hyp.desc}</p>
                <div className="mt-3 pt-2 border-t border-[#1e2c3e] flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>Criteria: Defined</span>
                  <span>Residual: Explicit</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Physical Baseline & Non-Overlapping Loss Principles */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-[#111822] border border-[#1e2c3e] rounded-lg p-5">
            <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-2 mb-3">
              <Sliders className="w-4 h-4 text-cyan-400" /> Physical Generation Baseline (Helios-1)
            </h2>
            <div className="bg-[#0b0f14] p-3 rounded border border-[#1e2c3e] font-mono text-xs text-cyan-300 overflow-x-auto">
              P_phys,i = min(P_cap,i, max(0, P_cap,i * (G_clean,i / 1000) * (1 + gamma * (T_mod,i - 25))))
            </div>
            <ul className="mt-4 space-y-2 text-xs text-slate-400">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                <span><strong>Rated Inverter Cap:</strong> Capped at 12.5 MW AC per block (P_cap = 12.5 MW).</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                <span><strong>Thermal Coefficient:</strong> gamma = -0.004 / °C relative to 25°C STC standard.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                <span><strong>Energy Semantics:</strong> Energy_MWh = AveragePower_MW * 0.25 (15-min interval).</span>
              </li>
            </ul>
          </div>

          <div className="bg-[#111822] border border-[#1e2c3e] rounded-lg p-5">
            <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-2 mb-3">
              <Layers className="w-4 h-4 text-cyan-400" /> Non-Overlapping Loss Waterfall
            </h2>
            <div className="bg-[#0b0f14] p-3 rounded border border-[#1e2c3e] font-mono text-xs text-slate-300">
              Total Shortfall = Weather + Curtailment + Equipment + Other + Unexplained Residual
            </div>
            <ul className="mt-4 space-y-2 text-xs text-slate-400">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                <span><strong>Zero Double-Counting:</strong> Mutually exclusive sequential accounting order.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                <span><strong>Explicit Residual:</strong> Never forced to zero without evidence.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                <span><strong>Bounded Recovery:</strong> Distinguishes observed, detectable, and actionable losses.</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Phase Boundary & Team Responsibilities Banner */}
        <div className="bg-[#172230]/60 border border-[#2b3f58] rounded-lg p-4 flex flex-col md:flex-row items-center justify-between text-xs text-slate-300 gap-4">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-cyan-400 shrink-0" />
            <div>
              <span className="font-semibold text-white">Phase 1 Foundation Operational:</span>
              <span className="text-slate-400 ml-1">
                Typed Pydantic contracts, deterministic temporal replay tests, and React/Tailwind workspace verified.
              </span>
            </div>
          </div>
          <div className="font-mono text-cyan-400 shrink-0">
            OWNERSHIP: 4-PERSON PARALLEL READY
          </div>
        </div>

      </main>

      {/* Industrial Footer */}
      <footer className="border-t border-[#1e2c3e] bg-[#0b0f14] px-6 py-3 text-xs text-slate-500 flex flex-col sm:flex-row justify-between items-center gap-2 font-mono">
        <div>AUDITRA // FIX PS3 Solar Incident Forensics</div>
        <div className="flex items-center gap-4 text-slate-400">
          <span>Heet Kakaria (Tech Lead)</span>
          <span>Amulya Dongre (Backend/Data)</span>
          <span>Atharva Hoge (Engine)</span>
          <span>Vedant Goyal (Frontend)</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
