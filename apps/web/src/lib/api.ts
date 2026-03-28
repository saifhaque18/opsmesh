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
  fingerprint: string | null;
  cluster_id: string | null;
  assigned_to: string | null;
  detected_at: string | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  ai_root_cause: string | null;
  ai_suggested_actions: string | null;
  ai_reviewed: boolean;
  processing_status: string | null;
  is_duplicate: boolean;
  duplicate_of: string | null;
  similarity_score: number | null;
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

// Cluster types
export interface Cluster {
  id: string;
  title: string;
  description: string | null;
  fingerprint: string;
  status: "active" | "merged" | "resolved";
  incident_count: number;
  max_severity_score: number | null;
  confidence: number;
  primary_service: string | null;
  primary_source: string | null;
  primary_environment: string | null;
  first_seen: string | null;
  last_seen: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClusterDetail extends Cluster {
  incidents: Incident[];
}

export interface ClusterListResponse {
  clusters: Cluster[];
  total: number;
  page: number;
  page_size: number;
}

export interface ClusterStats {
  total_clusters: number;
  active_clusters: number;
  total_duplicates: number;
  avg_cluster_size: number;
  largest_cluster_size: number;
}

export interface ClusterFilters {
  page?: number;
  page_size?: number;
  status?: string;
  service?: string;
  min_incidents?: number;
}

// Scoring types
export interface RuleResult {
  rule: string;
  score: number;
  weight: number;
  explanation: string;
}

export interface ScoringExplanation {
  final_score: number;
  severity_label: string;
  explanation: string;
  rules: RuleResult[];
  scored_at: string | null;
}

export interface ScoreHistoryEntry {
  id: string;
  score: number;
  previous_score: number | null;
  severity_label: string;
  source: string;
  scored_by: string | null;
  explanation: string | null;
  rule_details: Record<string, unknown> | null;
  override_reason: string | null;
  scored_at: string;
}

export interface ScoreHistoryResponse {
  incident_id: string;
  entries: ScoreHistoryEntry[];
  total: number;
}

export interface SeverityOverrideRequest {
  score: number;
  reason: string;
}

// Incident API functions
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

// Cluster API functions
export async function fetchClusters(
  filters: ClusterFilters = {}
): Promise<ClusterListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.append(key, String(value));
    }
  });
  const { data } = await api.get(`/api/v1/clusters?${params.toString()}`);
  return data;
}

export async function fetchCluster(id: string): Promise<ClusterDetail> {
  const { data } = await api.get(`/api/v1/clusters/${id}`);
  return data;
}

export async function fetchClusterStats(): Promise<ClusterStats> {
  const { data } = await api.get("/api/v1/clusters/stats");
  return data;
}

// Scoring API functions
export async function fetchScoringExplanation(
  incidentId: string
): Promise<ScoringExplanation> {
  const { data } = await api.get(`/api/v1/incidents/${incidentId}/scoring`);
  return data;
}

export async function fetchScoreHistory(
  incidentId: string
): Promise<ScoreHistoryResponse> {
  const { data } = await api.get(
    `/api/v1/incidents/${incidentId}/score-history`
  );
  return data;
}

export async function overrideSeverity(
  incidentId: string,
  request: SeverityOverrideRequest
): Promise<Incident> {
  const { data } = await api.post(
    `/api/v1/incidents/${incidentId}/override-severity`,
    request
  );
  return data;
}

export default api;
