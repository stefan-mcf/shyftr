export type Json = Record<string, unknown>;

const env = import.meta.env as Record<string, string | undefined>;
export const API_URL = env.VITE_SHYFTR_API_URL || "http://127.0.0.1:8014";
export const DEFAULT_ROOT = env.VITE_SHYFTR_CELL_ROOT || ".";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "content-type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(payload.message || payload.detail || response.statusText);
  }
  return payload as T;
}

function rootParam(root: string): string {
  return `root=${encodeURIComponent(root)}`;
}

export interface CellSummary {
  status: string;
  cell_id: string;
  cell_path: string;
  counts: Record<string, number>;
  grid_status: string;
  diagnostics: Json;
}

export interface CellList { status: string; cells: Array<{ cell_id: string; cell_type: string; cell_path: string }>; }
export interface RowList<T> { status: string; total: number; [key: string]: unknown; }
export interface Metrics { status: string; metrics: Record<string, number>; can_answer_improvement: boolean; }

export const api = {
  health: () => request<Json>("/health"),
  cells: (root: string) => request<CellList>(`/cells?${rootParam(root)}`),
  summary: (root: string, cellId: string) => request<CellSummary>(`/cell/${encodeURIComponent(cellId)}/summary?${rootParam(root)}`),
  sparks: (root: string, cellId: string, status = "") => request<RowList<Json>>(`/cell/${encodeURIComponent(cellId)}/sparks?${rootParam(root)}${status ? `&status=${encodeURIComponent(status)}` : ""}`),
  charges: (root: string, cellId: string, query = "") => request<RowList<Json>>(`/cell/${encodeURIComponent(cellId)}/charges?${rootParam(root)}${query ? `&query=${encodeURIComponent(query)}` : ""}`),
  hygiene: (root: string, cellId: string) => request<Json>(`/cell/${encodeURIComponent(cellId)}/hygiene?${rootParam(root)}`),
  sweep: (root: string, cellId: string) => request<Json>(`/cell/${encodeURIComponent(cellId)}/sweep?${rootParam(root)}`),
  proposals: (root: string, cellId: string) => request<RowList<Json>>(`/cell/${encodeURIComponent(cellId)}/proposals?${rootParam(root)}`),
  metrics: (root: string, cellId: string) => request<Metrics>(`/cell/${encodeURIComponent(cellId)}/metrics?${rootParam(root)}`),
  burden: (root: string, cellId: string) => request<Json>(`/cell/${encodeURIComponent(cellId)}/operator-burden?${rootParam(root)}`),
  policy: (root: string, cellId: string) => request<Json>(`/cell/${encodeURIComponent(cellId)}/policy-tuning?${rootParam(root)}`),
  pack: (root: string, cellId: string, body: Json) => request<Json>(`/cell/${encodeURIComponent(cellId)}/pack?${rootParam(root)}`, { method: "POST", body: JSON.stringify(body) }),
  signal: (root: string, cellId: string, body: Json) => request<Json>(`/cell/${encodeURIComponent(cellId)}/signal?${rootParam(root)}`, { method: "POST", body: JSON.stringify(body) }),
  ingest: (body: Json) => request<Json>("/ingest", { method: "POST", body: JSON.stringify(body) }),
  validate: (body: Json) => request<Json>("/validate", { method: "POST", body: JSON.stringify(body) }),
  reviewSpark: (root: string, cellId: string, sparkId: string, body: Json) => request<Json>(`/cell/${encodeURIComponent(cellId)}/sparks/${encodeURIComponent(sparkId)}/review?${rootParam(root)}`, { method: "POST", body: JSON.stringify(body) }),
  chargeAction: (root: string, cellId: string, chargeId: string, body: Json) => request<Json>(`/cell/${encodeURIComponent(cellId)}/charges/${encodeURIComponent(chargeId)}/action?${rootParam(root)}`, { method: "POST", body: JSON.stringify(body) }),
  decideProposal: (root: string, cellId: string, proposalId: string, body: Json) => request<Json>(`/cell/${encodeURIComponent(cellId)}/proposals/${encodeURIComponent(proposalId)}/decision?${rootParam(root)}`, { method: "POST", body: JSON.stringify(body) }),
};
