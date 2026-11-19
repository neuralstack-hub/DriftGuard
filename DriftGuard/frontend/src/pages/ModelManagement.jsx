import React, { useState } from "react";
import StatusBadge from "../components/StatusBadge";
import { api } from "../api/client";

export default function ModelManagement({ modelsData, onRefresh }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const versions = modelsData?.versions || [];
  const activeVersion = modelsData?.active_version;

  const runAction = async (fn, label) => {
    setBusy(true);
    setMsg("");
    try {
      await fn();
      setMsg(`${label} succeeded.`);
      await onRefresh();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Model Management</h2>
          <p className="text-sm text-slate-400">
            Version history, candidate evaluation, promotion, rejection, and rollback
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => runAction(() => api.triggerRetrain({ trigger_reason: "manual_retrain" }), "Manual Retrain")}
            disabled={busy}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-sm font-medium text-white"
          >
            Train Candidate Model
          </button>
          <button
            onClick={() => runAction(() => api.rollbackModel({ reason: "Dashboard rollback" }), "Rollback")}
            disabled={busy}
            className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-sm font-medium text-white"
          >
            Rollback to Previous
          </button>
        </div>
      </div>

      {msg && (
        <div className="p-3 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200">
          {msg}
        </div>
      )}

      <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-2.5 pr-4">Version</th>
              <th className="py-2.5 pr-4">Trained At</th>
              <th className="py-2.5 pr-4">MAE</th>
              <th className="py-2.5 pr-4">RMSE</th>
              <th className="py-2.5 pr-4">R²</th>
              <th className="py-2.5 pr-4">Status</th>
              <th className="py-2.5 pr-4">Notes</th>
              <th className="py-2.5">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {versions.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-400">
                  No model versions registered yet.
                </td>
              </tr>
            ) : (
              [...versions].reverse().map((v) => (
                <tr key={v.version}>
                  <td className="py-3 pr-4 font-semibold text-white">{v.version}</td>
                  <td className="py-3 pr-4 text-xs text-slate-400">{v.trained_at.slice(0, 19)}</td>
                  <td className="py-3 pr-4 text-slate-200">{v.metrics?.mae}</td>
                  <td className="py-3 pr-4 text-slate-200">{v.metrics?.rmse}</td>
                  <td className="py-3 pr-4 text-slate-200">{v.metrics?.r2}</td>
                  <td className="py-3 pr-4">
                    <StatusBadge status={v.status} />
                  </td>
                  <td className="py-3 pr-4 text-xs text-slate-400 max-w-xs truncate">{v.notes}</td>
                  <td className="py-3 flex gap-2">
                    {v.version !== activeVersion && (
                      <button
                        onClick={() => runAction(() => api.promoteModel(v.version), `Promote ${v.version}`)}
                        disabled={busy}
                        className="px-2.5 py-1 rounded bg-emerald-600/80 hover:bg-emerald-500 text-xs text-white"
                      >
                        Promote
                      </button>
                    )}
                    {v.version !== activeVersion && v.status !== "rejected" && (
                      <button
                        onClick={() => runAction(() => api.rejectModel(v.version), `Reject ${v.version}`)}
                        disabled={busy}
                        className="px-2.5 py-1 rounded bg-rose-600/80 hover:bg-rose-500 text-xs text-white"
                      >
                        Reject
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
