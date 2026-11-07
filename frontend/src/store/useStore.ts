import { create } from "zustand";
import { BaseData, SimulationData, TerrainData, TimelineItem } from "../types";
import { fetchBase, fetchModelsReport, fetchSeries, fetchSimulation, fetchTerrain } from "../services/api";

interface AppState {
  activeTab: "overview" | "ai";
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
  modelsReport: any | null;
  isLoading: boolean;

  setActiveTab: (tab: "overview" | "ai") => void;
  setHour: (hour: number) => void;
  togglePlay: () => void;
  setScale: (scale: number) => void;
  setThresholds: (lo: number, hi: number) => void;
  setRainAlert: (alert: number) => void;
  setSelectedArea: (name: string) => void;
  setViewMode: (mode: "3d" | "map") => void;
  setMetricMode: (mode: "risk" | "rain" | "terrain") => void;
  setScenarioModalOpen: (open: boolean) => void;

  initData: () => Promise<void>;
  updateSimulation: (newHour?: number) => Promise<void>;
}

export const useStore = create<AppState>((set, get) => ({
  activeTab: "overview",
  hour: 24,
  isPlaying: false,
  scale: 1.0,
  thresholdLow: 0.40,
  thresholdHigh: 0.70,
  rainAlert: 100,
  selectedAreaName: "Trà Mai",
  viewMode: "3d",
  metricMode: "risk",
  isScenarioModalOpen: false,

  baseData: null,
  terrainData: null,
  simData: null,
  seriesData: [],
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
