import React, { useCallback, useEffect, useState } from "react";
import { LogOut, RefreshCw } from "lucide-react";
import Sidebar from "./components/Sidebar";
import StatusBadge from "./components/StatusBadge";
import LoginPage from "./pages/LoginPage";
import Overview from "./pages/Overview";
import UploadDataset from "./pages/UploadDataset";
import ModelMonitoring from "./pages/ModelMonitoring";
import DriftDetection from "./pages/DriftDetection";
import ModelManagement from "./pages/ModelManagement";
import PipelineMonitoring from "./pages/PipelineMonitoring";
import Simulation from "./pages/Simulation";
import { api } from "./api/client";

const AUTH_REQUIRED = import.meta.env.VITE_AUTH_REQUIRED !== "false";

export default function App() {
  const [authUser, setAuthUser] = useState(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem("driftguard_auth") || "null");
      return saved?.token ? saved : null;
    } catch {
      sessionStorage.removeItem("driftguard_auth");
      return null;
    }
  });
  const [activePage, setActivePage] = useState("overview");
  const [overview, setOverview] = useState(null);
  const [projectsData, setProjectsData] = useState({ active_project: "beijing-pm25", projects: [] });
  const [modelsData, setModelsData] = useState(null);
  const [driftData, setDriftData] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [apiError, setApiError] = useState("");
  const [workspaceLoaded, setWorkspaceLoaded] = useState(false);

  const loadAll = useCallback(async () => {
    if (AUTH_REQUIRED && !authUser) return;
    try {
      const [ov, pr, md, dr, pl] = await Promise.all([
        api.getOverview(),
        api.getProjects(),
        api.getModels(),
        api.getDriftHistory(),
        api.getPipelineHistory(),
      ]);
      setOverview(ov);
      setProjectsData(pr);
      setModelsData(md);
      setDriftData(dr);
      setPipelineData(pl);
      setApiError("");
    } catch (err) {
      if (err.status === 401 && AUTH_REQUIRED) {
        sessionStorage.removeItem("driftguard_auth");
        setAuthUser(null);
        return;
      }
      setApiError(`Backend unreachable: ${err.message}`);
    } finally {
      setWorkspaceLoaded(true);
    }
  }, [authUser]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const handleLoginSuccess = (userData) => {
    sessionStorage.setItem("driftguard_auth", JSON.stringify(userData));
    setWorkspaceLoaded(false);
    setAuthUser(userData);
  };

  const handleLogout = async () => {
    try { await api.logout(); } catch { /* Clear the local session even if the API is offline. */ }
    sessionStorage.removeItem("driftguard_auth");
    setAuthUser(null);
  };

  const handleProjectSwitch = async (e) => {
    const projectId = e.target.value;
    try {
      await api.activateProject(projectId);
      await loadAll();
    } catch (err) {
      setApiError(`Failed to switch project: ${err.message}`);
    }
  };

  if (AUTH_REQUIRED && !authUser) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="flex min-h-screen bg-[#f3f4f6] text-slate-900">
      <Sidebar
        activePage={activePage}
        onSelect={setActivePage}
        activeDataset={overview?.active_dataset_name}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-slate-200 px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500">
            <label className="inline-flex items-center gap-2">
              <span className="font-medium text-slate-600">Dataset Project:</span>
              <select
                value={projectsData.active_project}
                onChange={handleProjectSwitch}
                className="px-2.5 py-1 rounded-lg border border-slate-300 bg-white text-slate-900 text-xs font-semibold"
              >
                {projectsData.projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <span className="text-slate-300">|</span>
            <span>
              Active Model:{" "}
              <strong className="text-slate-900">{overview?.active_model_version || "None"}</strong>
            </span>
            <span className="text-slate-300">|</span>
            <span className="inline-flex items-center gap-1.5">
              Health: <StatusBadge status={overview?.overall_health || "No Model"} />
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadAll}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-medium text-slate-700 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
            {AUTH_REQUIRED && <button
                onClick={handleLogout}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-rose-50 hover:text-rose-600 text-xs font-medium text-slate-700 transition"
              >
                <LogOut className="w-3.5 h-3.5" />
                Logout
              </button>}
          </div>
        </header>

        <main className="flex-1 p-6 lg:p-8 overflow-y-auto">
          {apiError && (
            <div className="mb-6 p-3.5 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-800 flex flex-wrap items-center justify-between gap-3" role="alert">
              <span>{apiError}</span>
              <button onClick={loadAll} className="px-3 py-1.5 rounded-md border border-amber-300 bg-white text-xs font-semibold hover:bg-amber-100 transition">Try again</button>
            </div>
          )}

          {!workspaceLoaded ? (
            <div className="rounded-xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500" role="status">
              <RefreshCw className="mx-auto mb-3 h-5 w-5 animate-spin text-slate-400" />
              Loading your workspace…
            </div>
          ) : <>
          {activePage === "overview" && (
            <Overview overview={overview} modelsData={modelsData} onRefresh={loadAll} />
          )}
          {activePage === "upload" && (
            <UploadDataset onRefresh={loadAll} onNavigate={setActivePage} />
          )}
          {activePage === "monitoring" && (
            <ModelMonitoring overview={overview} modelsData={modelsData} driftData={driftData} />
          )}
          {activePage === "drift" && (
            <DriftDetection driftData={driftData} onRefresh={loadAll} />
          )}
          {activePage === "models" && (
            <ModelManagement modelsData={modelsData} onRefresh={loadAll} />
          )}
          {activePage === "pipeline" && (
            <PipelineMonitoring pipelineData={pipelineData} />
          )}
          {activePage === "simulation" && <Simulation onRefresh={loadAll} />}
          </>}
        </main>
      </div>
    </div>
  );
}
