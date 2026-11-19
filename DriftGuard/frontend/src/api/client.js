const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const headers = isFormData
    ? { ...(options.headers || {}) }
    : { "Content-Type": "application/json", ...(options.headers || {}) };

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  login: (username, password) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  getOverview: () => request("/api/overview"),
  getProjects: () => request("/api/projects"),
  activateProject: (projectId) => request(`/api/projects/${projectId}/activate`, { method: "POST" }),
  getModels: () => request("/api/models"),
  trainV1: () => request("/api/models/train-v1", { method: "POST" }),
  promoteModel: (version) => request(`/api/models/${version}/promote`, { method: "POST" }),
  rejectModel: (version) => request(`/api/models/${version}/reject`, { method: "POST" }),
  rollbackModel: (payload = {}) =>
    request("/api/models/rollback", { method: "POST", body: JSON.stringify(payload) }),
  getDriftHistory: () => request("/api/drift/history"),
  checkDrift: () => request("/api/drift/check", { method: "POST" }),
  checkUploadedDrift: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/drift/check-upload", { method: "POST", body: form });
  },
  simulateDrift: (payload) =>
    request("/api/drift/simulate", { method: "POST", body: JSON.stringify(payload) }),
  getPipelineHistory: () => request("/api/pipeline/history"),
  triggerRetrain: (payload = {}) =>
    request("/api/pipeline/retrain", { method: "POST", body: JSON.stringify(payload) }),
  predictPm25: (payload) =>
    request("/api/predict", { method: "POST", body: JSON.stringify(payload) }),
  inspectDataset: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/datasets/inspect", { method: "POST", body: form });
  },
  uploadAndTrainDataset: ({ file, datasetName, targetColumn, selectedFeatures }) => {
    const form = new FormData();
    form.append("file", file);
    form.append("dataset_name", datasetName);
    form.append("target_column", targetColumn);
    form.append("selected_features", JSON.stringify(selectedFeatures));
    return request("/api/datasets/upload-and-train", { method: "POST", body: form });
  },
};
