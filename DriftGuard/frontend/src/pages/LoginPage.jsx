import React, { useState } from "react";
import { Activity, GitBranch, Lock, RefreshCw, ShieldCheck, Upload } from "lucide-react";
import { api } from "../api/client";

const HIGHLIGHTS = [
  {
    icon: Upload,
    title: "Custom Dataset & Model Onboarding",
    desc: "Upload any labelled CSV, select target and feature columns, and train a versioned RandomForestRegressor.",
  },
  {
    icon: Activity,
    title: "Statistical Drift Detection",
    desc: "Compare reference training distributions against incoming production batches using KS-test, PSI, and Wasserstein distance.",
  },
  {
    icon: RefreshCw,
    title: "Automated Retraining & Evaluation Gate",
    desc: "Retrain on labelled data and promote candidate models only when they outperform the active model on a fixed validation set.",
  },
  {
    icon: GitBranch,
    title: "Version Control, Rollback & CI/CD",
    desc: "Maintain immutable v1/v2/v3 artifacts, roll back safely, and dispatch GitHub Actions workflows.",
  },
];

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("driftguard123");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await api.login(username, password);
      onLoginSuccess(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f3f4f6] flex flex-col justify-center py-10 px-4 sm:px-8">
      <div className="max-w-5xl w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left: About DriftGuard */}
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-600 text-white shadow-sm">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-900">DriftGuard</h1>
              <p className="text-sm font-medium text-blue-600">
                Automated ML Model Monitoring &amp; Self-Healing Platform
              </p>
            </div>
          </div>

          <p className="text-slate-600 text-base leading-relaxed">
            DriftGuard helps developers and ML engineers detect when real-world input distributions
            shift away from training data, automate retraining on labelled data, and protect
            production by promoting only validated improvements.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {HIGHLIGHTS.map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-1.5"
              >
                <div className="flex items-center gap-2 text-blue-600 font-semibold text-sm">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{title}</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Login Card */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-2xl p-7 shadow-sm space-y-5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Sign In to Dashboard</h2>
              <p className="text-xs text-slate-500">Access model monitoring &amp; retraining</p>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Username</span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 text-sm"
              />
            </label>

            <label className="block text-sm">
              <span className="font-medium text-slate-700">Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 text-sm"
              />
            </label>

            <button
              type="submit"
              disabled={busy}
              className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-sm font-semibold text-white shadow-sm transition"
            >
              {busy ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="text-xs text-slate-400 text-center">
            Default demo credentials: <code className="text-slate-600">admin</code> /{" "}
            <code className="text-slate-600">driftguard123</code> (configurable in <code>.env</code>)
          </p>
        </div>
      </div>
    </div>
  );
}
