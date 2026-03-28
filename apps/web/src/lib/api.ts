import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export interface Incident {
  id: string;
  title: string;
  description: string | null;
  source: string;
  status: "open" | "acknowledged" | "investigating" | "resolved" | "closed";
  severity: "critical" | "high" | "medium" | "low" | "info";
  severity_score: number | null;
  service: string | null;
  environment: string | null;
  region: string | null;
  assigned_to: string | null;
  detected_at: string | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  ai_root_cause: string | null;
  ai_suggested_actions: string | null;
  ai_reviewed: boolean;
  processing_status: string | null;
  created_at: string;
  updated_at: string;
}

export interface IncidentListResponse {
  incidents: Incident[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface IncidentStats {
  total: number;
  open: number;
  acknowledged: number;
  investigating: number;
  resolved: number;
  closed: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface IncidentFilters {
  page?: number;
  page_size?: number;
  status?: string;
  severity?: string;
  source?: string;
  service?: string;
  environment?: string;
  search?: string;
}

export async function fetchIncidents(
  filters: IncidentFilters = {}
): Promise<IncidentListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "" && value !== null) {
      params.append(key, String(value));
    }
  });
  const { data } = await api.get(`/api/v1/incidents?${params.toString()}`);
  return data;
}

export async function fetchIncidentStats(): Promise<IncidentStats> {
  const { data } = await api.get("/api/v1/incidents/stats");
  return data;
}

export async function fetchIncident(id: string): Promise<Incident> {
  const { data } = await api.get(`/api/v1/incidents/${id}`);
  return data;
}

export default api;
