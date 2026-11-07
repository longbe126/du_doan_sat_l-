import { BaseData, SimulationData, TerrainData, TimelineItem } from "../types";

const BASE_URL = "/api";

export async function fetchBase(): Promise<BaseData> {
  const res = await fetch(`${BASE_URL}/base`);
  if (!res.ok) throw new Error("Failed to load base data");
  return res.json();
}

export async function fetchTerrain(): Promise<TerrainData> {
  const res = await fetch(`${BASE_URL}/terrain`);
  if (!res.ok) throw new Error("Failed to load terrain data");
  return res.json();
}

export async function fetchSimulation(
  hour: number,
  scale: number,
  lo: number,
  hi: number,
  rainAlert: number = 100
): Promise<SimulationData> {
  const params = new URLSearchParams({
    hour: hour.toString(),
    scale: scale.toString(),
    lo: lo.toString(),
    hi: hi.toString(),
    rain_alert: rainAlert.toString(),
  });
  const res = await fetch(`${BASE_URL}/simulation?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to load simulation data");
  return res.json();
}

export async function fetchSeries(
  scale: number,
  lo: number,
  hi: number
): Promise<{ timeline: TimelineItem[] }> {
  const params = new URLSearchParams({
    scale: scale.toString(),
    lo: lo.toString(),
    hi: hi.toString(),
  });
  const res = await fetch(`${BASE_URL}/series?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to load series data");
  return res.json();
}

export async function fetchModelsReport(): Promise<any> {
  const res = await fetch(`${BASE_URL}/models`);
  if (!res.ok) throw new Error("Failed to load models report");
  return res.json();
}
