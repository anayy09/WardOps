import { create } from "zustand";

interface CommandState {
  // Timeline state
  currentTime: Date;
  isPlaying: boolean;
  playbackSpeed: number;
  zoomLevel: "6h" | "12h" | "24h";
  
  // Selection state
  selectedPatientId: number | null;
  selectedBedId: number | null;
  selectedScenarioId: number | null;
  
  // UI state
  showCopilot: boolean;
  
  // Actions
  setCurrentTime: (time: Date) => void;
  setIsPlaying: (playing: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
  setZoomLevel: (level: "6h" | "12h" | "24h") => void;
  setSelectedPatientId: (id: number | null) => void;
  setSelectedBedId: (id: number | null) => void;
  setSelectedScenarioId: (id: number | null) => void;
  setShowCopilot: (show: boolean) => void;
  
  // Playback controls
  play: () => void;
  pause: () => void;
  stepForward: () => void;
  stepBackward: () => void;
}

export const useCommandStore = create<CommandState>((set, get) => ({
  // Initial state
  currentTime: new Date("2026-01-15T08:00:00"),
  isPlaying: false,
  playbackSpeed: 1,
  zoomLevel: "24h",
  selectedPatientId: null,
  selectedBedId: null,
  selectedScenarioId: null,
  showCopilot: true,
  
  // Actions
  setCurrentTime: (time) => set({ currentTime: time }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),
  setZoomLevel: (level) => set({ zoomLevel: level }),
  setSelectedPatientId: (id) => set({ selectedPatientId: id }),
  setSelectedBedId: (id) => set({ selectedBedId: id }),
  setSelectedScenarioId: (id) => set({ selectedScenarioId: id }),
  setShowCopilot: (show) => set({ showCopilot: show }),
  
  // Playback controls
  play: () => set({ isPlaying: true }),
  pause: () => set({ isPlaying: false }),
  stepForward: () => {
    const { currentTime } = get();
    const newTime = new Date(currentTime);
    newTime.setMinutes(newTime.getMinutes() + 15);
    set({ currentTime: newTime });
  },
  stepBackward: () => {
    const { currentTime } = get();
    const newTime = new Date(currentTime);
    newTime.setMinutes(newTime.getMinutes() - 15);
    set({ currentTime: newTime });
  },
}));
