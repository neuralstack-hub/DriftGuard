import React, { useCallback, useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import Overview from "./pages/Overview";
import ModelMonitoring from "./pages/ModelMonitoring";
import DriftDetection from "./pages/DriftDetection";
import ModelManagement from "./pages/ModelManagement";
import PipelineMonitoring from "./pages/PipelineMonitoring";
import Simulation from "./pages/Simulation";
import { api } from "./api/client";

export default function App() {
  const [activePage, setActivePage] = useState("overview");
  const [overview, setOverview] = useState(null);
  const [modelsData, setModelsData] = useState(null);
  const [driftData, setDriftData] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [apiError, setApiError] = useState("");

  const loadAll = useCallback(async () => {
    try {
      const [ov, md, dr, pl] = await Promise.all([
        api.getOverview(),
        api.getModels(),
        api.getDriftHistory(),
        api.getPipelineHistory(),
      ]);
      setOverview(ov);
      setModelsData(md);
      setDriftData(dr);
      setPipelineData(pl);
      setApiError("");
    } catch (err) {
      setApiError(`Backend unreachable: ${err.message}`);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  return (
    <div className="flex min-h-screen bg-[#0b1120] text-slate-100">
      <Sidebar activePage={activePage} onSelect={setActivePage} />
      <main className="flex-1 p-6 lg:p-8 overflow-y-auto">
        {apiError && (
          <div className="mb-6 p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-sm text-amber-300">
            {apiError}
          </div>
        )}

        {activePage === "overview" && (
          <Overview overview={overview} modelsData={modelsData} onRefresh={loadAll} />
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
      </main>
    </div>
  );
}
