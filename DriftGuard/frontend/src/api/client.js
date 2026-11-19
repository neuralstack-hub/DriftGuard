const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  getOverview: () => request("/api/overview"),
  getModels: () => request("/api/models"),
  trainV1: () => request("/api/models/train-v1", { method: "POST" }),
  promoteModel: (version) => request(`/api/models/${version}/promote`, { method: "POST" }),
  rejectModel: (version) => request(`/api/models/${version}/reject`, { method: "POST" }),
  rollbackModel: (payload = {}) =>
    request("/api/models/rollback", { method: "POST", body: JSON.stringify(payload) }),
  getDriftHistory: () => request("/api/drift/history"),
  checkDrift: () => request("/api/drift/check", { method: "POST" }),
  simulateDrift: (payload) =>
    request("/api/drift/simulate", { method: "POST", body: JSON.stringify(payload) }),
  getPipelineHistory: () => request("/api/pipeline/history"),
  triggerRetrain: (payload = {}) =>
    request("/api/pipeline/retrain", { method: "POST", body: JSON.stringify(payload) }),
  predictPm25: (payload) =>
    request("/api/predict", { method: "POST", body: JSON.stringify(payload) }),
};
