import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import MetricCard from "../components/MetricCard";
import StatusBadge from "../components/StatusBadge";

export default function ModelMonitoring({ overview, modelsData, driftData }) {
  const activeVersion = overview?.active_model_version;
  const activeRecord = (modelsData?.versions || []).find((v) => v.version === activeVersion);
  const driftHistory = driftData?.history || [];

  const trendData = driftHistory.map((d, idx) => ({
    check: `#${idx + 1}`,
    driftScore: d.drift_score,
    threshold: d.drift_threshold,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Model Monitoring</h2>
        <p className="text-sm text-slate-400">
          Active deployment telemetry, validation metrics, and drift score trajectory
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Version"
          value={activeRecord?.version || "None"}
          subtitle={activeRecord ? `Trained: ${activeRecord.trained_at.slice(0, 10)}` : "Not deployed"}
          accent="emerald"
        />
        <MetricCard
          title="MAE / RMSE"
          value={
            activeRecord
              ? `${activeRecord.metrics.mae} / ${activeRecord.metrics.rmse}`
              : "—"
          }
          subtitle="Fixed 2014 validation set"
          accent="sky"
        />
        <MetricCard
          title="R² Score"
          value={activeRecord?.metrics?.r2 ?? "—"}
          subtitle="Coefficient of determination"
          accent="slate"
        />
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Monitoring Status
          </p>
          <div className="mt-2">
            <StatusBadge status={overview?.drift_status || "STABLE"} />
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Note: Data drift does not automatically mean accuracy has dropped.
          </p>
        </div>
      </div>

      <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
        <h3 className="text-base font-semibold text-white mb-4">Drift Score Over Time</h3>
        {trendData.length === 0 ? (
          <p className="text-sm text-slate-400 py-10 text-center">
            No drift checks recorded yet. Run a drift check or simulation.
          </p>
        ) : (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="check" stroke="#94a3b8" />
                <YAxis domain={[0, 1]} stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                <Line
                  type="monotone"
                  dataKey="driftScore"
                  name="Drift Score"
                  stroke="#f43f5e"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="threshold"
                  name="Threshold"
                  stroke="#f59e0b"
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
