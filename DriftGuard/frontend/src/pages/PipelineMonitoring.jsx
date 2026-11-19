import React from "react";
import StatusBadge from "../components/StatusBadge";

export default function PipelineMonitoring({ pipelineData }) {
  const retraining = pipelineData?.retraining_history || [];
  const deployments = pipelineData?.deployment_logs || [];
  const ghRuns = pipelineData?.github_actions_runs || [];
  const rollbacks = pipelineData?.rollback_history || [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Pipeline Monitoring</h2>
        <p className="text-sm text-slate-500">
          GitHub Actions dispatches, automated retraining runs, deployment logs, and rollbacks
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 mb-3">Retraining History</h3>
          {retraining.length === 0 ? (
            <p className="text-sm text-slate-500">No retraining runs yet.</p>
          ) : (
            <div className="space-y-2.5 max-h-72 overflow-y-auto">
              {[...retraining].reverse().map((r, i) => (
                <div key={i} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-900">
                      {r.candidate_version} (vs {r.previous_active_version})
                    </span>
                    <StatusBadge status={r.decision} />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Trigger: {r.trigger_reason} | Candidate RMSE: {r.candidate_metrics?.rmse} vs Active RMSE:{" "}
                    {r.active_metrics_on_fixed_val?.rmse}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 mb-3">GitHub Actions Dispatch Status</h3>
          {ghRuns.length === 0 ? (
            <p className="text-sm text-slate-500">No GitHub Actions dispatches triggered yet.</p>
          ) : (
            <div className="space-y-2.5 max-h-72 overflow-y-auto">
              {[...ghRuns].reverse().map((g, i) => (
                <div key={i} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-900">{g.event_type}</span>
                    <StatusBadge status={g.status} />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{g.message}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 mb-3">System &amp; Deployment Logs</h3>
          {deployments.length === 0 ? (
            <p className="text-sm text-slate-500">No deployment events recorded.</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {[...deployments].reverse().map((d, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
                  <span className="font-semibold text-blue-600">{d.version}</span>{" "}
                  <span className="text-slate-500">[{d.action}]</span> — {d.details}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 mb-3">Rollback History</h3>
          {rollbacks.length === 0 ? (
            <p className="text-sm text-slate-500">No rollbacks executed.</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {[...rollbacks].reverse().map((rb, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                  <span className="font-semibold text-amber-700">
                    {rb.from_version} → {rb.to_version}
                  </span>{" "}
                  <span className="text-slate-400">({rb.timestamp.slice(0, 19)})</span>
                  <p className="text-slate-600 mt-0.5">{rb.reason}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
