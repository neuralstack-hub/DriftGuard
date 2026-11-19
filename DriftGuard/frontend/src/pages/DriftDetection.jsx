import React, { useRef, useState } from "react";
import StatusBadge from "../components/StatusBadge";
import { api } from "../api/client";

export default function DriftDetection({ driftData, onRefresh }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);
  const history = driftData?.history || [];
  const latest = history.length > 0 ? history[history.length - 1] : null;

  const handleCheck = async () => {
    setBusy(true);
    setError("");
    try {
      await api.checkDrift();
      await onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleUploadCheck = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      await api.checkUploadedDrift(file);
      await onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Drift Detection</h2>
          <p className="text-sm text-slate-500">
            Reference training distribution vs incoming production data or uploaded CSV batch (KS test + PSI)
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleUploadCheck}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={busy}
            className="px-4 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50 text-sm font-medium text-slate-700 shadow-sm transition"
          >
            Upload Incoming CSV
          </button>
          <button
            onClick={handleCheck}
            disabled={busy}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-sm font-medium text-white shadow-sm transition"
          >
            {busy ? "Checking..." : "Run Production Drift Check"}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-sm text-rose-700">
          {error}
        </div>
      )}

      {latest ? (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Latest Feature Drift Breakdown</h3>
              <p className="text-xs text-slate-500">
                Source: {latest.source} | Drift Score: {latest.drift_score} (Threshold:{" "}
                {latest.drift_threshold})
              </p>
            </div>
            <StatusBadge status={latest.dataset_drift_detected ? "DRIFT DETECTED" : "STABLE"} />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-2.5 pr-4">Feature</th>
                  <th className="py-2.5 pr-4">Ref Mean</th>
                  <th className="py-2.5 pr-4">Incoming Mean</th>
                  <th className="py-2.5 pr-4">KS Stat</th>
                  <th className="py-2.5 pr-4">p-value</th>
                  <th className="py-2.5 pr-4">PSI</th>
                  <th className="py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {latest.features.map((f) => (
                  <tr key={f.feature}>
                    <td className="py-2.5 pr-4 font-medium text-slate-900">{f.feature}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{f.reference_mean}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{f.current_mean}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{f.ks_statistic}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{f.p_value}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{f.psi}</td>
                    <td className="py-2.5">
                      <StatusBadge status={f.drift_detected ? "DRIFT DETECTED" : "STABLE"} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm text-center text-sm text-slate-500">
          No drift checks recorded yet. Upload an incoming CSV, run a production drift check, or use the Simulation tab.
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-3">Drift History</h3>
        {history.length === 0 ? (
          <p className="text-sm text-slate-500">No history entries.</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {[...history].reverse().map((h, i) => (
              <div
                key={i}
                className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-lg bg-slate-50 border border-slate-200 text-sm"
              >
                <div>
                  <span className="font-medium text-slate-900">{h.source}</span>
                  <span className="ml-3 text-xs text-slate-500">{h.timestamp}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-600">
                    Score: {h.drift_score} ({h.drifted_features_count}/{h.total_features_monitored})
                  </span>
                  <StatusBadge status={h.dataset_drift_detected ? "DRIFT DETECTED" : "STABLE"} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
