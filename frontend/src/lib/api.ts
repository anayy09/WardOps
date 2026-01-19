const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data?: T;
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// Demo endpoints
export const demoApi = {
  getStatus: () => fetchApi<ApiResponse<{ is_loaded: boolean; patient_count: number; event_count: number }>>("/api/demo/status"),
  loadDemo: (seed: number = 42) => fetchApi<ApiResponse<any>>("/api/demo/load", {
    method: "POST",
    body: JSON.stringify({ seed }),
  }),
  clearDemo: () => fetchApi<ApiResponse<any>>("/api/demo/clear", { method: "DELETE" }),
};

// Unit/Bed endpoints
export const unitApi = {
  getUnits: () => fetchApi<any[]>("/api/units"),
  getUnit: (id: number) => fetchApi<any>(`/api/units/${id}`),
  getBeds: (unitId: number) => fetchApi<any[]>(`/api/units/${unitId}/beds`),
};

// Patient endpoints
export const patientApi = {
  getPatients: (params?: { unit_id?: number; active_only?: boolean; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.unit_id) searchParams.set("unit_id", params.unit_id.toString());
    if (params?.active_only !== undefined) searchParams.set("active_only", params.active_only.toString());
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    return fetchApi<any[]>(`/api/patients?${searchParams}`);
  },
  getPatient: (id: number) => fetchApi<any>(`/api/patients/${id}`),
  getPatientTrace: (id: number) => fetchApi<any>(`/api/patients/${id}/trace`),
};

// Events endpoints
export const eventApi = {
  getEvents: (params?: { unit_id?: number; patient_id?: number; start_time?: string; end_time?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.unit_id) searchParams.set("unit_id", params.unit_id.toString());
    if (params?.patient_id) searchParams.set("patient_id", params.patient_id.toString());
    if (params?.start_time) searchParams.set("start_time", params.start_time);
    if (params?.end_time) searchParams.set("end_time", params.end_time);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    return fetchApi<any[]>(`/api/events?${searchParams}`);
  },
};

// Nurse endpoints
export const nurseApi = {
  getNurses: (unitId?: number) => {
    const params = unitId ? `?unit_id=${unitId}` : "";
    return fetchApi<any[]>(`/api/nurses${params}`);
  },
};

// Metrics endpoints
export const metricsApi = {
  getKPI: (unitId: number = 1, timestamp?: string) => {
    const params = timestamp ? `?unit_id=${unitId}&timestamp=${timestamp}` : `?unit_id=${unitId}`;
    return fetchApi<any>(`/api/metrics/kpi${params}`);
  },
};

// Scenario endpoints
export const scenarioApi = {
  getScenarios: () => fetchApi<any[]>("/api/scenarios"),
  getScenario: (id: number) => fetchApi<any>(`/api/scenarios/${id}`),
  createScenario: (data: any) => fetchApi<any>("/api/scenarios", {
    method: "POST",
    body: JSON.stringify(data),
  }),
  updateScenario: (id: number, data: any) => fetchApi<any>(`/api/scenarios/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  }),
  deleteScenario: (id: number) => fetchApi<any>(`/api/scenarios/${id}`, { method: "DELETE" }),
  getScenarioResults: (id: number) => fetchApi<any>(`/api/scenarios/${id}/results`),
};

// Simulation endpoints
export const simulationApi = {
  runSimulation: (scenarioId: number, baselineId?: number) => {
    if (!scenarioId) {
      throw new Error("scenarioId is required");
    }
    const params = baselineId ? `?scenario_id=${scenarioId}&baseline_id=${baselineId}` : `?scenario_id=${scenarioId}`;
    return fetchApi<any>(`/api/simulation/run${params}`, { method: "POST" });
  },
  getStatus: (jobId: number) => fetchApi<any>(`/api/simulation/${jobId}/status`),
  getResults: (scenarioId: number) => fetchApi<any>(`/api/simulation/${scenarioId}/results`),
  cancelSimulation: (jobId: number) => fetchApi<any>(`/api/simulation/${jobId}`, { method: "DELETE" }),
};

// Copilot endpoints
export const copilotApi = {
  getStatus: () => fetchApi<{ available: boolean; model: string | null }>("/api/copilot/status"),
  chat: (messages: { role: string; content: string }[], includeTools: boolean = true) =>
    fetchApi<any>("/api/copilot/chat", {
      method: "POST",
      body: JSON.stringify({ messages, include_tools: includeTools }),
    }),
  getTools: () => fetchApi<any>("/api/copilot/tools"),
};

// WebSocket URL
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
