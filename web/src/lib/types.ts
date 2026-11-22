export type Level = "verde" | "amarillo" | "naranja" | "rojo";

export type Snapshot = {
  rain_acc_mm: number;
  intensity_mm_h: number;
  burst_mm_30min: number;
  soil_moisture: number;
  data_age_min: number;
  sensor_quality: number;
};

export type Factor = {
  id: string;
  label: string;
  points: number;
  detail: string;
};

export type Modifier = {
  id: string;
  label: string;
  value: number;
  factor: number;
  detail: string;
};

export type ZoneScore = {
  zone_id: string;
  name: string;
  kind: string;
  index: number;
  level: Level;
  operational_level: Level;
  confidence: number;
  confidence_note: string | null;
  reaction_margin_min: number;
  concentration_min: number;
  fast_trigger: boolean;
  fast_trigger_reason: string | null;
  exposure: number;
  attention: number;
  svg: string;
  label: number[];
  snapshot: Snapshot;
  factors: Factor[];
  modifiers: Modifier[];
};

export type Frame = {
  index: number;
  label: string;
  minute: number;
  narrative: string;
  zones: ZoneScore[];
};

export type ScenarioMeta = {
  id: string;
  title: string;
  summary: string;
  demo_hint: string;
  step_minutes: number;
  frame_count: number;
};

export type ScenarioDetail = ScenarioMeta & {
  frames: Frame[];
};

export const LEVEL_LABEL: Record<Level, string> = {
  verde: "Verde",
  amarillo: "Amarillo",
  naranja: "Naranja",
  rojo: "Rojo",
};

export const LEVEL_COLOR: Record<Level, string> = {
  verde: "#1f9d62",
  amarillo: "#d6a63a",
  naranja: "#e07a32",
  rojo: "#d4544c",
};

export const LEVEL_INK = "#0a0f0c";

export const LEVELS: Level[] = ["verde", "amarillo", "naranja", "rojo"];
