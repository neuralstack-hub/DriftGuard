import React, { useEffect, useState } from "react";
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

const DEFAULT_PM25_INPUT = {
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
};

export default function Overview({ overview, modelsData, onRefresh }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const schema = overview?.active_schema;
  const isCustom = Boolean(schema?.is_custom);

  const [predInput, setPredInput] = useState(DEFAULT_PM25_INPUT);
  const [customInput, setCustomInput] = useState({});
  const [predResult, setPredResult] = useState(null);

  useEffect(() => {
    if (isCustom && schema?.raw_features) {
      const initial = {};
      schema.raw_features.forEach((f) => {
        const cats = schema.categorical_categories?.[f];
        initial[f] = cats ? cats[0] || "" : 0;
      });
      setCustomInput(initial);
      setPredResult(null);
    }
  }, [isCustom, schema?.dataset_name]);

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
      let payload;
      if (isCustom) {
        payload = {};
        for (const [k, v] of Object.entries(customInput)) {
          payload[k] = schema.categorical_categories?.[k] ? v : Number(v);
        }
      } else {
        payload = {
          ...predInput,
          month: Number(predInput.month),
          day: Number(predInput.day),
          hour: Number(predInput.hour),
          DEWP: Number(predInput.DEWP),
          TEMP: Number(predInput.TEMP),
          PRES: Number(predInput.PRES),
          Iws: Number(predInput.Iws),
        };
      }
      const res = await api.predictPm25(payload);
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
  const importanceData = overview?.feature_importance || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Dashboard Overview</h2>
          <p className="text-sm text-slate-500">
            Dataset: <span className="text-slate-800 font-medium">{overview?.active_dataset_name || "Beijing PM2.5"}</span>{" "}
            · Target: <span className="text-slate-800 font-medium">{overview?.active_target_column || "pm2.5"}</span>
          </p>
        </div>
        {!isCustom && (
          <button
            onClick={handleTrainV1}
            disabled={busy}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-sm font-medium text-white shadow-sm transition"
          >
            {busy ? "Training Model v1..." : "Initialize / Train Model v1"}
          </button>
        )}
      </div>

      {message && (
        <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-sm text-blue-800">
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Overall Health</p>
          <div className="mt-2">
            <StatusBadge status={overview?.overall_health || "No Model"} />
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Active: {overview?.active_model_version || "None"} ({overview?.total_monitored_models ?? 0} versions)
          </p>
        </div>
        <MetricCard
          title="Current Performance (RMSE)"
          value={overview?.active_model_metrics?.rmse ?? "—"}
          subtitle={
            overview?.active_model_metrics
              ? `MAE: ${overview.active_model_metrics.mae} | R²: ${overview.active_model_metrics.r2}`
              : "Train a model to evaluate"
          }
          accent="slate"
        />
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Drift Status</p>
          <div className="mt-2">
            <StatusBadge status={overview?.drift_status || "STABLE"} />
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Score: {overview?.latest_drift_score ?? 0} (Threshold: {overview?.drift_threshold ?? 0.3})
          </p>
        </div>
        <MetricCard
          title="Retraining Runs"
          value={overview?.total_retraining_runs ?? 0}
          subtitle={`Rollbacks: ${overview?.total_rollbacks ?? 0}`}
          accent="blue"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Model Version Error Comparison</h3>
          {chartData.length === 0 ? (
            <p className="text-sm text-slate-500 py-12 text-center">
              No models trained yet. Train Model v1 or upload a custom CSV dataset.
            </p>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="version" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", color: "#0f172a" }} />
                  <Bar dataKey="RMSE" fill="#2563eb" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="MAE" fill="#93c5fd" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Top Feature Importance</h3>
          {importanceData.length === 0 ? (
            <p className="text-sm text-slate-500 py-12 text-center">
              Train a model to inspect which features drive predictions.
            </p>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={importanceData} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" stroke="#64748b" />
                  <YAxis dataKey="feature" type="category" width={95} stroke="#64748b" tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", color: "#0f172a" }} />
                  <Bar dataKey="importance" fill="#10b981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-4">
          Live Prediction ({overview?.active_target_column || "pm2.5"})
        </h3>
        <form onSubmit={handlePredict} className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-sm">
          {isCustom && schema?.raw_features ? (
            schema.raw_features.slice(0, 12).map((feat) => {
              const cats = schema.categorical_categories?.[feat];
              return cats ? (
                <label key={feat} className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-slate-600 truncate">{feat}</span>
                  <select
                    value={customInput[feat] ?? cats[0] ?? ""}
                    onChange={(e) => setCustomInput({ ...customInput, [feat]: e.target.value })}
                    className="px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900"
                  >
                    {cats.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </label>
              ) : (
                <label key={feat} className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-slate-600 truncate">{feat}</span>
                  <input
                    type="number"
                    step="any"
                    value={customInput[feat] ?? 0}
                    onChange={(e) => setCustomInput({ ...customInput, [feat]: e.target.value })}
                    className="px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900"
                  />
                </label>
              );
            })
          ) : (
            <>
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
                  <span className="text-xs font-medium text-slate-600">{label}</span>
                  <input
                    type="number"
                    step="any"
                    value={predInput[key]}
                    onChange={(e) => setPredInput({ ...predInput, [key]: e.target.value })}
                    className="px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900"
                  />
                </label>
              ))}
              <label className="flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-600">Wind Dir</span>
                <select
                  value={predInput.cbwd}
                  onChange={(e) => setPredInput({ ...predInput, cbwd: e.target.value })}
                  className="px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-900"
                >
                  <option value="NW">NW</option>
                  <option value="NE">NE</option>
                  <option value="SE">SE</option>
                  <option value="cv">cv</option>
                </select>
              </label>
            </>
          )}

          <div className="col-span-2 sm:col-span-4 lg:col-span-6 flex items-center justify-between pt-2">
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm transition"
            >
              Predict
            </button>
            {predResult && (
              <div className="text-right">
                <span className="text-lg font-bold text-blue-600">
                  {predResult.predicted_value ?? predResult.predicted_pm25}
                </span>
                <p className="text-xs text-slate-500">via {predResult.model_version}</p>
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
