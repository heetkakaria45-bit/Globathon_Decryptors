/**
 * AUDITRA Frontend Domain Types
 * Owner: Vedant Goyal (Frontend Lead)
 * Synced with: backend/app/schemas.py (Heet Kakaria)
 */

export type HypothesisId =
  | 'H1_EQUIPMENT_DERATING'
  | 'H2_WEATHER_DROP'
  | 'H3_GRID_CURTAILMENT'
  | 'H4_SENSOR_DRIFT'
  | 'H5_FORECAST_BIAS'
  | 'H6_UNEXPLAINED_RESIDUAL';

export type HypothesisStatus =
  | 'SUPPORTED'
  | 'CONTRADICTED'
  | 'INCONCLUSIVE'
  | 'INSUFFICIENT_DATA';

export type EvidenceQuality = 'VALIDATED' | 'SUSPECT' | 'DEGRADED' | 'MISSING';

export type SensorProvenance =
  | 'PRIMARY_PYRANOMETER'
  | 'SECONDARY_PYRANOMETER'
  | 'SATELLITE_NOWCAST'
  | 'INVERTER_SCADA'
  | 'WEATHER_STATION'
  | 'GRID_DISPATCH_SYSTEM'
  | 'FORECAST_ENGINE';

export type LossCategory =
  | 'WEATHER_VARIANCE'
  | 'GRID_CURTAILMENT'
  | 'EQUIPMENT_DERATING'
  | 'OTHER_VALIDATED'
  | 'UNEXPLAINED_RESIDUAL';

export interface EvidenceRecord {
  evidence_id: string;
  event_time: string; // ISO-8601 UTC string
  available_at: string; // ISO-8601 UTC string
  source: SensorProvenance;
  quality: EvidenceQuality;
  metric_name: string;
  metric_value: number;
  unit: string;
  block_id?: string;
  description: string;
}

export interface HypothesisResult {
  hypothesis_id: HypothesisId;
  title: string;
  status: HypothesisStatus;
  confidence_score?: number | null;
  ruling_criteria: string;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  missing_evidence: string[];
  summary: string;
}

export interface LossCategoryItem {
  category: LossCategory;
  loss_mwh: number;
  equivalent_power_mw: number;
  percentage_of_shortfall: number;
  ruling_basis: string;
}

export interface LossAttribution {
  total_forecast_energy_mwh: number;
  total_actual_energy_mwh: number;
  total_shortfall_mwh: number;
  weather_loss_mwh: number;
  curtailment_loss_mwh: number;
  equipment_loss_mwh: number;
  other_validated_loss_mwh: number;
  unexplained_residual_mwh: number;
  breakdown: LossCategoryItem[];
  precedence_order: LossCategory[];
}

export interface RecoveryEstimate {
  observed_loss_mwh: number;
  detectable_loss_mwh: number;
  actionable_loss_mwh: number;
  preventable_loss_mwh: number;
  recoverable_energy_mwh_min: number;
  recoverable_energy_mwh_max: number;
  limiting_factors: string[];
  assumptions: string[];
}

export interface PlantMetricSummary {
  forecast_power_mw: number;
  forecast_energy_mwh: number;
  physical_baseline_power_mw: number;
  physical_baseline_energy_mwh: number;
  actual_power_mw: number;
  actual_energy_mwh: number;
  grid_dispatch_limit_mw: number;
  curtailment_active: boolean;
}

export interface ReplayRequest {
  scenario_id: string;
  replay_time: string; // ISO-8601 UTC
  include_evidence_log?: boolean;
}

export interface ReplayResponse {
  scenario_id: string;
  replay_time: string; // ISO-8601 UTC
  model_version: string;
  plant_id: string;
  total_scenario_evidence_count: number;
  eligible_evidence_count: number;
  plant_metrics: PlantMetricSummary;
  loss_attribution: LossAttribution;
  hypotheses: HypothesisResult[];
  recovery_estimate: RecoveryEstimate;
  eligible_evidence?: EvidenceRecord[];
}

export interface ScenarioSummary {
  scenario_id: string;
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  incident_category: string;
}
