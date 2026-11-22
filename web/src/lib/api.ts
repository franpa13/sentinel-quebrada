import type { ScenarioDetail, ScenarioMeta, Snapshot, ZoneScore } from "@/lib/types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function readJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `El motor respondió ${response.status}.`);
  }
  return response.json() as Promise<T>;
}

export function listScenarios() {
  return readJson<{ scenarios: ScenarioMeta[] }>("/scenarios");
}

export function getScenario(id: string) {
  return readJson<ScenarioDetail>(`/scenarios/${id}`);
}

export function evaluate(snapshot: Snapshot) {
  return readJson<{ narrative: string; zones: ZoneScore[]; note: string }>("/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ snapshot }),
  });
}

export function openMeteo() {
  return readJson<{
    disclaimer: string;
    narrative: string;
    zones: ZoneScore[];
    snapshot: Snapshot;
  }>("/context/open-meteo");
}
