import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  demoApi,
  unitApi,
  patientApi,
  eventApi,
  nurseApi,
  metricsApi,
  scenarioApi,
  simulationApi,
  copilotApi,
} from "@/lib/api";

// Demo hooks
export function useDemoStatus() {
  return useQuery({
    queryKey: ["demo", "status"],
    queryFn: demoApi.getStatus,
  });
}

export function useLoadDemo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ seed }: { seed: number }) => demoApi.loadDemo(seed),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["demo"] });
      queryClient.invalidateQueries({ queryKey: ["units"] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });
}

// Unit hooks
export function useUnits() {
  return useQuery({
    queryKey: ["units"],
    queryFn: unitApi.getUnits,
  });
}

export function useUnit(id: number) {
  return useQuery({
    queryKey: ["units", id],
    queryFn: () => unitApi.getUnit(id),
    enabled: !!id,
  });
}

export function useBeds(unitId: number) {
  return useQuery({
    queryKey: ["units", unitId, "beds"],
    queryFn: () => unitApi.getBeds(unitId),
    enabled: !!unitId,
    refetchInterval: 5000, // Poll every 5s
  });
}

// Patient hooks
export function usePatients(params?: { unit_id?: number; active_only?: boolean; limit?: number }) {
  return useQuery({
    queryKey: ["patients", params],
    queryFn: () => patientApi.getPatients(params),
  });
}

export function usePatient(id: number) {
  return useQuery({
    queryKey: ["patients", id],
    queryFn: () => patientApi.getPatient(id),
    enabled: !!id,
  });
}

export function usePatientTrace(id: number) {
  return useQuery({
    queryKey: ["patients", id, "trace"],
    queryFn: () => patientApi.getPatientTrace(id),
    enabled: !!id,
  });
}

// Event hooks
export function useEvents(params?: { unit_id?: number; patient_id?: number; start_time?: string; end_time?: string; limit?: number }) {
  return useQuery({
    queryKey: ["events", params],
    queryFn: () => eventApi.getEvents(params),
  });
}

// Nurse hooks
export function useNurses(unitId?: number) {
  return useQuery({
    queryKey: ["nurses", unitId],
    queryFn: () => nurseApi.getNurses(unitId),
  });
}

// Metrics hooks
export function useKPIMetrics(unitId: number = 1, timestamp?: string) {
  return useQuery({
    queryKey: ["metrics", "kpi", unitId, timestamp],
    queryFn: () => metricsApi.getKPI(unitId, timestamp),
    refetchInterval: 10000, // Poll every 10s
  });
}

// Scenario hooks
export function useScenarios() {
  return useQuery({
    queryKey: ["scenarios"],
    queryFn: scenarioApi.getScenarios,
  });
}

export function useScenario(id: number) {
  return useQuery({
    queryKey: ["scenarios", id],
    queryFn: () => scenarioApi.getScenario(id),
    enabled: !!id,
  });
}

export function useCreateScenario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: scenarioApi.createScenario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenarios"] });
    },
  });
}

export function useScenarioResults(id: number) {
  return useQuery({
    queryKey: ["scenarios", id, "results"],
    queryFn: () => scenarioApi.getScenarioResults(id),
    enabled: id > 0, // Only query if id is a valid positive number
    retry: false, // Don't retry on error
    staleTime: Infinity, // Never consider data stale (no background refetch)
    refetchOnWindowFocus: false, // Don't refetch when window regains focus
    refetchOnMount: false, // Don't refetch when component mounts
    refetchOnReconnect: false, // Don't refetch on reconnect
  });
}

// Simulation hooks
export function useRunSimulation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ scenarioId, baselineId }: { scenarioId: number; baselineId?: number }) =>
      simulationApi.runSimulation(scenarioId, baselineId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["simulations"] });
    },
  });
}

export function useSimulationStatus(jobId: number) {
  return useQuery({
    queryKey: ["simulations", jobId, "status"],
    queryFn: () => simulationApi.getStatus(jobId),
    enabled: !!jobId,
    refetchInterval: (data: any) => {
      if (data?.status === "completed" || data?.status === "failed") {
        return false;
      }
      return 1000; // Poll every second while running
    },
  });
}

// Copilot hooks
export function useCopilotStatus() {
  return useQuery({
    queryKey: ["copilot", "status"],
    queryFn: copilotApi.getStatus,
  });
}

export function useCopilotChat() {
  return useMutation({
    mutationFn: ({ messages, includeTools }: { messages: { role: string; content: string }[]; includeTools?: boolean }) =>
      copilotApi.chat(messages, includeTools),
  });
}

// Parse scenario from text
export function useParseScenarioText() {
  return useMutation({
    mutationFn: async (text: string) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/copilot/parse-scenario`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!response.ok) throw new Error("Failed to parse scenario");
      return response.json();
    },
  });
}

// Generate comparison narrative
export function useGenerateNarrative() {
  return useMutation({
    mutationFn: async ({ baselineId, scenarioId }: { baselineId: number; scenarioId: number }) => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/copilot/compare-narrative`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ baseline_id: baselineId, scenario_id: scenarioId }),
        }
      );
      if (!response.ok) throw new Error("Failed to generate narrative");
      return response.json();
    },
  });
}
