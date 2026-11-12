import { create } from "zustand";
import { BaseData, SeriesData, SimulationData, TerrainData, TimelineItem } from "../types";
import { fetchBase, fetchModelsReport, fetchSeries, fetchSimulation, fetchTerrain } from "../services/api";

interface AppState {
  activeTab: "overview" | "history" | "ai";
  hour: number;
  isPlaying: boolean;
  scale: number;
  thresholdLow: number;
  thresholdHigh: number;
  rainAlert: number;
  selectedAreaName: string;
  viewMode: "3d" | "map";
  metricMode: "risk" | "rain" | "terrain";
  isScenarioModalOpen: boolean;

  baseData: BaseData | null;
  terrainData: TerrainData | null;
  simData: SimulationData | null;
  seriesData: TimelineItem[];
  fullSeries: SeriesData | null;
  modelsReport: any | null;
  isLoading: boolean;

  setActiveTab: (tab: "overview" | "history" | "ai") => void;
  setHour: (hour: number) => void;
  togglePlay: () => void;
  setScale: (scale: number) => void;
  setThresholds: (lo: number, hi: number) => void;
  setRainAlert: (alert: number) => void;
  setSelectedArea: (name: string) => void;
  setViewMode: (mode: "3d" | "map") => void;
  setMetricMode: (mode: "risk" | "rain" | "terrain") => void;
  setScenarioModalOpen: (open: boolean) => void;
  applyScenario: (scale: number, lo: number, hi: number, rainAlert: number) => Promise<void>;
  focusEventOnMap: (lat: number, lon: number) => void;

  initData: () => Promise<void>;
  updateSimulation: (newHour?: number) => Promise<void>;
}

export const useStore = create<AppState>((set, get) => ({
  activeTab: "overview",
  hour: 24,
  isPlaying: false,
  scale: 1.0,
  thresholdLow: 0.25,
  thresholdHigh: 0.45,
  rainAlert: 100,
  selectedAreaName: "Trà Mai",
  viewMode: "3d",
  metricMode: "risk",
  isScenarioModalOpen: false,

  baseData: null,
  terrainData: null,
  simData: null,
  seriesData: [],
  fullSeries: null,
  modelsReport: null,
  isLoading: true,

  setActiveTab: (tab) => set({ activeTab: tab }),
  setHour: (hour) => {
    set({ hour });
    get().updateSimulation(hour);
  },
  togglePlay: () => set((state) => ({ isPlaying: !state.isPlaying })),
  setScale: (scale) => {
    set({ scale });
    get().updateSimulation();
  },
  setThresholds: (thresholdLow, thresholdHigh) => {
    set({ thresholdLow, thresholdHigh });
    get().updateSimulation();
  },
  setRainAlert: (rainAlert) => {
    set({ rainAlert });
    get().updateSimulation();
  },
  setSelectedArea: (selectedAreaName) => set({ selectedAreaName }),
  setViewMode: (viewMode) => set({ viewMode }),
  setMetricMode: (metricMode) => set({ metricMode }),
  setScenarioModalOpen: (isScenarioModalOpen) => set({ isScenarioModalOpen }),

  focusEventOnMap: (lat: number, lon: number) => {
    const { baseData } = get();
    if (baseData?.areas?.length) {
      let closest = baseData.areas[0];
      let minDist = Infinity;
      for (const a of baseData.areas) {
        const d = Math.hypot(a.lat - lat, a.lon - lon);
        if (d < minDist) {
          minDist = d;
          closest = a;
        }
      }
      set({ selectedAreaName: closest.name, activeTab: "overview" });
    } else {
      set({ activeTab: "overview" });
    }
  },

  applyScenario: async (newScale: number, newLow: number, newHigh: number, newRainAlert: number) => {
    const { hour } = get();
    set({
      scale: newScale,
      thresholdLow: newLow,
      thresholdHigh: newHigh,
      rainAlert: newRainAlert,
    });
    try {
      const [sim, series] = await Promise.all([
        fetchSimulation(hour, newScale, newLow, newHigh, newRainAlert),
        fetchSeries(newScale, newLow, newHigh),
      ]);
      set({
        simData: sim,
        seriesData: series.timeline,
        fullSeries: series,
        isScenarioModalOpen: false,
      });
    } catch (err) {
      console.error("Failed to apply scenario:", err);
      set({ isScenarioModalOpen: false });
    }
  },

  initData: async () => {
    set({ isLoading: true });
    try {
      const [base, terrain, sim, series, models] = await Promise.all([
        fetchBase(),
        fetchTerrain(),
        fetchSimulation(get().hour, get().scale, get().thresholdLow, get().thresholdHigh, get().rainAlert),
        fetchSeries(get().scale, get().thresholdLow, get().thresholdHigh),
        fetchModelsReport(),
      ]);

      const defaultArea = sim.max_risk_area ? sim.max_risk_area.name : (base.areas[0]?.name || "Trà Mai");
      set({
        baseData: base,
        terrainData: terrain,
        simData: sim,
        seriesData: series.timeline,
        fullSeries: series,
        modelsReport: models,
        selectedAreaName: defaultArea,
        viewMode: "3d",
        isLoading: false,
      });
    } catch (err) {
      console.error("Failed to init data:", err);
      set({ isLoading: false });
    }
  },

  updateSimulation: async (newHour?: number) => {
    const { hour, scale, thresholdLow, thresholdHigh, rainAlert } = get();
    const h = newHour !== undefined ? newHour : hour;
    try {
      const sim = await fetchSimulation(h, scale, thresholdLow, thresholdHigh, rainAlert);
      set({ simData: sim });
    } catch (err) {
      console.error("Failed to update simulation:", err);
    }
  },
}));
