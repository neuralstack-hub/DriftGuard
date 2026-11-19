import React, { useState } from "react";
import StatusBadge from "../components/StatusBadge";
import { api } from "../api/client";

export default function Simulation({ onRefresh }) {
  const [intensity, setIntensity] = useState(1.2);
  const [autoRetrain, setAutoRetrain] = useState(true);
  const [simulateWorse, setSimulateWorse] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleSimulate = async () => {
    setBusy(true);
    setError("");
    try {
      const res = await api.simulateDrift({
        intensity: Number(intensity),
        n_samples: 500,
        auto_retrain: autoRetrain,
        simulate_worse_candidate: simulateWorse,
      });
      setResult(res);
      await onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Drift &amp; Self-Healing Simulation</h2>
        <p className="text-sm text-slate-500">
          Generate shifted incoming feature distributions, run statistical drift detection, and observe automated retraining &amp; evaluation
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              Shift Intensity ({intensity}x)
            </label>
            <input
              type="range"
              min="0.4"
              max="2.5"
              step="0.1"
              value={intensity}
              onChange={(e) => setIntensity(e.target.value)}
              className="w-full accent-blue-600"
            />
          </div>

          <label className="flex items-center gap-2.5 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRetrain}
              onChange={(e) => setAutoRetrain(e.target.checked)}
              className="rounded accent-blue-600"
            />
            <span>Auto-trigger retraining when drift is detected</span>
          </label>

          <label className="flex items-center gap-2.5 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={simulateWorse}
              onChange={(e) => setSimulateWorse(e.target.checked)}
              className="rounded accent-rose-600"
            />
            <span>Simulate degraded candidate (test rejection gate)</span>
          </label>
        </div>

        <button
          onClick={handleSimulate}
          disabled={busy}
          className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-sm font-semibold text-white shadow-sm transition"
        >
          {busy ? "Running Simulation & Pipeline..." : "Simulate Drift"}
        </button>

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-sm text-rose-700">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-900">1. Drift Detection Output</h3>
              <StatusBadge
                status={result.drift_result.dataset_drift_detected ? "DRIFT DETECTED" : "STABLE"}
              />
            </div>
            <p className="text-sm text-slate-700">
              Drift Score: <strong>{result.drift_result.drift_score}</strong> (
              {result.drift_result.drifted_features_count} /{" "}
              {result.drift_result.total_features_monitored} features drifted)
            </p>
            <p className="text-xs text-slate-500">{result.drift_result.note}</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-900">2. Retraining Pipeline Result</h3>
              {result.retraining_result?.decision && (
                <StatusBadge status={result.retraining_result.decision} />
              )}
            </div>
            {result.retraining_result ? (
              result.retraining_result.error ? (
                <p className="text-sm text-rose-600">{result.retraining_result.error}</p>
              ) : (
                <div className="text-sm text-slate-700 space-y-1">
                  <p>
                    Candidate: <strong>{result.retraining_result.candidate_version}</strong> (vs{" "}
                    {result.retraining_result.previous_active_version})
                  </p>
                  <p>
                    Candidate RMSE: <strong>{result.retraining_result.candidate_metrics.rmse}</strong>{" "}
                    | Active RMSE:{" "}
                    <strong>{result.retraining_result.active_metrics_on_fixed_val.rmse}</strong>
                  </p>
                  <p className="text-xs text-slate-500">
                    GitHub Dispatch: {result.retraining_result.github_dispatch?.status}
                  </p>
                </div>
              )
            ) : (
              <p className="text-sm text-slate-500">Auto-retraining was not triggered.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
