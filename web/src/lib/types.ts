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

export type RouteBand = "baja" | "media" | "alta" | "muy_alta" | "atencion";

export type RouteWeek = {
  place: { name: string; latitude: number; longitude: number };
  on_rn9: boolean;
  distance_to_rn9_km: number;
  chance: number | null;
  band: Exclude<RouteBand, "atencion"> | null;
  operational: RouteBand | null;
  headline: string;
  factors: Factor[];
  analogs: {
    episode: string;
    date: string;
    place: string;
    kind: string;
    distance_km: number;
    summary: string;
    source: string;
    url: string;
  }[];
  limits: string[];
  week: {
    from: string | null;
    to: string | null;
    peak_day: string | null;
    peak_index: number | null;
    rain_sum_mm: number | null;
  };
  days: RouteDay[];
  aluvional: {
    headline: string;
    terrain: { slope_deg: number | null; elevation_m: number | null; susceptibility: number; note: string };
    soil: { value: number; day: string | null; note: string };
  };
};

export type RouteDay = {
  date: string | null;
  rain_mm: number | null;
  index: number | null;
  chance: number | null;
  band: Exclude<RouteBand, "atencion"> | null;
  operational: RouteBand;
  factors: Factor[];
  note: string | null;
};

export type Cut = {
  episode: string;
  date: string;
  place: string;
  lat: number;
  lon: number;
  kind: string;
  summary: string;
  source: string;
  url: string;
};

export type Pueblo = {
  name: string;
  lat: number;
  lon: number;
  episodes_near: number;
  route_km: number;
  off_route_km: number;
  route_point: [number, number];
};

export type Traza = { coordinates: [number, number][]; km: number[]; attribution: string; note: string };

export type TripDay = {
  date: string;
  chance: number | null;
  operational: RouteBand;
  driver: string | null;
  complete: boolean;
  max_rain_mm: number | null;
  towns: { name: string; chance: number | null; operational: RouteBand; rain_mm: number | null }[];
};

export type Trip = {
  from: string;
  to: string;
  stops: string[];
  chance: number | null;
  operational: RouteBand;
  worst_day: string | null;
  best_day: string | null;
  headline: string;
  days: TripDay[];
  towns: RouteWeek[];
  cortes: Cut[];
  limits: string[];
};

export const BAND_LABEL: Record<RouteBand, string> = {
  baja: "Baja",
  media: "Media",
  alta: "Alta",
  muy_alta: "Muy alta",
  atencion: "Atención",
};

export const BAND_COLOR: Record<RouteBand, string> = {
  baja: "#1f9d62",
  media: "#d6a63a",
  alta: "#e07a32",
  muy_alta: "#d4544c",
  atencion: "#3f86a3",
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
