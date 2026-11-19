import React, { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import MetricCard from "../components/MetricCard";
import StatusBadge from "../components/StatusBadge";
import { api } from "../api/client";

export default function Overview({ overview, modelsData, onRefresh }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [predInput, setPredInput] = useState({
    month: 11,
    day: 15,
    hour: 14,
    DEWP: -6,
    TEMP: 4,
    PRES: 1022,
    cbwd: "NW",
    Iws: 12.5,
    Is: 0,
    Ir: 0,
  });
  const [predResult, setPredResult] = useState(null);

  const handleTrainV1 = async () => {
    setBusy(true);
    setMessage("");
    try {
      const res = await api.trainV1();
      setMessage(`Model ${res.model.version} (${res.status}) — RMSE: ${res.model.metrics.rmse}`);
      await onRefresh();
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      const res = await api.predictPm25({
        ...predInput,
        month: Number(predInput.month),
        day: Number(predInput.day),
        hour: Number(predInput.hour),
        DEWP: Number(predInput.DEWP),
        TEMP: Number(predInput.TEMP),
        PRES: Number(predInput.PRES),
        Iws: Number(predInput.Iws),
      });
      setPredResult(res);
    } catch (err) {
      setMessage(`Prediction error: ${err.message}`);
    }
  };

  const versions = modelsData?.versions || [];
  const chartData = versions.map((v) => ({
    version: v.version,
    RMSE: v.metrics?.rmse ?? 0,
    MAE: v.metrics?.mae ?? 0,
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Platform Overview</h2>
          <p className="text-sm text-slate-400">
            Real-time model health, drift status, and PM2.5 inference
          </p>
        </div>
        <button
          onClick={handleTrainV1}
          disabled={busy}
          className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-sm font-medium text-white transition"
        >
          {busy ? "Training Model v1..." : "Initialize / Train Model v1"}
        </button>
      </div>

      {message && (
        <div className="p-3 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200">
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Monitored Models"
          value={overview?.total_monitored_models ?? 0}
          subtitle={`Retraining runs: ${overview?.total_retraining_runs ?? 0}`}
          accent="sky"
        />
        <MetricCard
          title="Active Model Version"
          value={overview?.active_model_version || "None"}
          subtitle={overview?.dataset_present ? "Beijing PM2.5 dataset ready" : "Dataset missing"}
          accent="emerald"
        />
        <MetricCard
          title="Current Performance (RMSE)"
          value={overview?.active_model_metrics?.rmse ?? "—"}
          subtitle={
            overview?.active_model_metrics
              ? `MAE: ${overview.active_model_metrics.mae} | R²: ${overview.active_model_metrics.r2}`
              : "Train Model v1 to evaluate"
          }
          accent="slate"
        />
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">Drift Status</p>
          <div className="mt-2">
            <StatusBadge status={overview?.drift_status || "STABLE"} />
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Score: {overview?.latest_drift_score ?? 0} (Threshold: {overview?.drift_threshold ?? 0.3})
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <h3 className="text-base font-semibold text-white mb-4">Model Version Error Comparison</h3>
          {chartData.length === 0 ? (
            <p className="text-sm text-slate-400 py-12 text-center">
              No models trained yet. Click &ldquo;Initialize / Train Model v1&rdquo; above.
            </p>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="version" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }}
                  />
                  <Bar dataKey="RMSE" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="MAE" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <h3 className="text-base font-semibold text-white mb-4">Live PM2.5 Prediction</h3>
          <form onSubmit={handlePredict} className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
            {[
              ["month", "Month"],
              ["day", "Day"],
              ["hour", "Hour"],
              ["TEMP", "Temp (°C)"],
              ["DEWP", "Dew Point (°C)"],
              ["PRES", "Pressure (hPa)"],
              ["Iws", "Wind Speed"],
            ].map(([key, label]) => (
              <label key={key} className="flex flex-col gap-1">
                <span className="text-xs text-slate-400">{label}</span>
                <input
                  type="number"
                  step="any"
                  value={predInput[key]}
                  onChange={(e) => setPredInput({ ...predInput, [key]: e.target.value })}
                  className="px-2.5 py-1.5 rounded bg-slate-900 border border-slate-700 text-slate-100"
                />
              </label>
            ))}
            <label className="flex flex-col gap-1">
              <span className="text-xs text-slate-400">Wind Dir</span>
              <select
                value={predInput.cbwd}
                onChange={(e) => setPredInput({ ...predInput, cbwd: e.target.value })}
                className="px-2.5 py-1.5 rounded bg-slate-900 border border-slate-700 text-slate-100"
              >
                <option value="NW">NW</option>
                <option value="NE">NE</option>
                <option value="SE">SE</option>
                <option value="cv">cv</option>
              </select>
            </label>
            <div className="col-span-2 sm:col-span-3 flex items-center justify-between pt-2">
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium transition"
              >
                Predict PM2.5
              </button>
              {predResult && (
                <div className="text-right">
                  <span className="text-lg font-bold text-emerald-400">
                    {predResult.predicted_pm25} {predResult.unit}
                  </span>
                  <p className="text-xs text-slate-400">via {predResult.model_version}</p>
                </div>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
