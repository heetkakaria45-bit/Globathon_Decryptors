/**
 * AUDITRA API Service
 * Handles HTTP requests to the FastAPI backend.
 */

import { ReplayRequest, ReplayResponse, ScenarioSummary } from '../types/schemas';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with status ${res.status}`);
  }
  return res.json();
}

export async function fetchScenarios(): Promise<ScenarioSummary[]> {
  const res = await fetch(`${API_BASE_URL}/api/scenarios`);
  if (!res.ok) {
    throw new Error(`Failed to fetch scenarios: ${res.statusText}`);
  }
  return res.json();
}

export async function replayInvestigation(payload: ReplayRequest): Promise<ReplayResponse> {
  const res = await fetch(`${API_BASE_URL}/api/replay`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Replay failed with status ${res.status}`);
  }

  return res.json();
}
