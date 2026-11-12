export interface Area {
  code: string;
  name: string;
  lat: number;
  lon: number;
  cover: string;
  elev: number;
  slope: number;
  score?: number;
  prev_score?: number;
  delta_score?: number;
  level?: "Thấp" | "Trung bình" | "Cao";
  rain?: number;
}

export interface SimLogEvent {
  hour: number;
  time: string;
  area: string;
  type: string;
  text: string;
  sub: string;
  color: string;
}

export interface SimulationData {
  hour: number;
  time_str: string;
  scale: number;
  thresholds: { low: number; high: number };
  areas: Area[];
  grid_risk: number[];
  grid_cells: number[];
  grid_distribution: {
    low: number;
    mid: number;
    high: number;
    total: number;
  };
  area_counts: {
    low: number;
    mid: number;
    high: number;
    total: number;
  };
  max_risk_area: {
    name: string;
    code: string;
    score: number;
    delta: number;
    level: string;
  };
  max_rain_area: {
    name: string;
    code: string;
    rain: number;
    delta: number;
  };
  top3_risk: Array<{
    name: string;
    code: string;
    score: number;
    delta: number;
    level: string;
  }>;
  rain_exceeded_count: number;
  events_log: SimLogEvent[];
  total_events: number;
}

export interface TerrainData {
  rows: number;
  cols: number;
  elev_min: number;
  elev_max: number;
  elevation: number[];
  slope: number[];
  lat: number[];
  lon: number[];
}

export interface BaseData {
  areas: Area[];
  events: Array<{
    id: string;
    date: string;
    lat: number;
    lon: number;
    elev: number;
    cause: string;
    damage: number;
  }>;
  metadata: Record<string, any>;
  model_name: string;
  trained_at: string;
  bounds: {
    lat_min: number;
    lat_max: number;
    lon_min: number;
    lon_max: number;
  };
}

export interface TimelineItem {
  hour: number;
  time: string;
  low: number;
  mid: number;
  high: number;
  total: number;
  max_score: number;
}

export interface SeriesData {
  timeline: TimelineItem[];
  scores_by_area?: Record<string, number[]>;
  rain_by_area?: Record<string, number[]>;
  max_scores?: number[];
  max_rain?: number[];
  n_high_areas?: number[];
  high_cells?: number[];
}
