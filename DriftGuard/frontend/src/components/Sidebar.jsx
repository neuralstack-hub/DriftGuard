import React from "react";
import {
  Activity,
  AlertTriangle,
  FlaskConical,
  GitBranch,
  Layers,
  LayoutDashboard,
  ShieldCheck,
} from "lucide-react";

const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "monitoring", label: "Model Monitoring", icon: Activity },
  { id: "drift", label: "Drift Detection", icon: AlertTriangle },
  { id: "models", label: "Model Management", icon: Layers },
  { id: "pipeline", label: "Pipeline Monitoring", icon: GitBranch },
  { id: "simulation", label: "Simulation", icon: FlaskConical },
];

export default function Sidebar({ activePage, onSelect }) {
  return (
    <aside className="w-64 shrink-0 bg-[#0f172a] border-r border-slate-800 flex flex-col min-h-screen">
      <div className="px-6 py-5 border-b border-slate-800 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-emerald-500/15 text-emerald-400">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white">DriftGuard</h1>
          <p className="text-xs text-slate-400">MLOps Self-Healing</p>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
          const active = activePage === id;
          return (
            <button
              key={id}
              onClick={() => onSelect(id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                  : "text-slate-300 hover:bg-slate-800/70 hover:text-white"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800 text-xs text-slate-500">
        <p className="font-medium text-slate-400">Use Case</p>
        <p>Beijing PM2.5 Air Quality</p>
        <p className="mt-1">RandomForestRegressor</p>
      </div>
    </aside>
  );
}
