import React, { useState } from "react";
import StatusBadge from "../components/StatusBadge";
import { api } from "../api/client";

export default function DriftDetection({ driftData, onRefresh }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
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

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Drift Detection</h2>
          <p className="text-sm text-slate-400">
            Reference training distribution (2010–2012) vs incoming production data (KS test + PSI)
          </p>
        </div>
        <button
          onClick={handleCheck}
          disabled={busy}
          className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-sm font-medium text-white transition"
        >
          {busy ? "Checking..." : "Run Production Drift Check"}
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-sm text-rose-300">
          {error}
        </div>
      )}

      {latest ? (
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-base font-semibold text-white">Latest Feature Drift Breakdown</h3>
              <p className="text-xs text-slate-400">
                Source: {latest.source} | Drift Score: {latest.drift_score} (Threshold:{" "}
                {latest.drift_threshold})
              </p>
            </div>
            <StatusBadge status={latest.dataset_drift_detected ? "DRIFT DETECTED" : "STABLE"} />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
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
              <tbody className="divide-y divide-slate-800/80">
                {latest.features.map((f) => (
                  <tr key={f.feature}>
                    <td className="py-2.5 pr-4 font-medium text-white">{f.feature}</td>
                    <td className="py-2.5 pr-4 text-slate-300">{f.reference_mean}</td>
                    <td className="py-2.5 pr-4 text-slate-300">{f.current_mean}</td>
                    <td className="py-2.5 pr-4 text-slate-300">{f.ks_statistic}</td>
                    <td className="py-2.5 pr-4 text-slate-300">{f.p_value}</td>
                    <td className="py-2.5 pr-4 text-slate-300">{f.psi}</td>
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
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-8 text-center text-sm text-slate-400">
          No drift checks recorded yet. Run a production drift check or use the Simulation tab.
        </div>
      )}

      <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
        <h3 className="text-base font-semibold text-white mb-3">Drift History</h3>
        {history.length === 0 ? (
          <p className="text-sm text-slate-400">No history entries.</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {[...history].reverse().map((h, i) => (
              <div
                key={i}
                className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-lg bg-slate-900/70 border border-slate-800 text-sm"
              >
                <div>
                  <span className="font-medium text-white">{h.source}</span>
                  <span className="ml-3 text-xs text-slate-400">{h.timestamp}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-300">
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
