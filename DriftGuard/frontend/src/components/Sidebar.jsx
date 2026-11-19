import React from "react";
import {
  Activity,
  AlertTriangle,
  FlaskConical,
  GitBranch,
  Layers,
  LayoutDashboard,
  ShieldCheck,
  Upload,
} from "lucide-react";

const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "upload", label: "Upload Dataset", icon: Upload },
  { id: "monitoring", label: "Model Monitoring", icon: Activity },
  { id: "drift", label: "Drift Detection", icon: AlertTriangle },
  { id: "models", label: "Model Management", icon: Layers },
  { id: "pipeline", label: "Pipeline Monitoring", icon: GitBranch },
  { id: "simulation", label: "Simulation", icon: FlaskConical },
];

export default function Sidebar({ activePage, onSelect, activeDataset }) {
  return (
    <aside className="w-64 shrink-0 bg-white border-r border-slate-200 flex flex-col min-h-screen">
      <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-blue-600 text-white shadow-sm">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-slate-900">DriftGuard</h1>
          <p className="text-xs text-slate-500">MLOps Platform</p>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
          const active = activePage === id;
          return (
            <button
              key={id}
              onClick={() => onSelect(id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-blue-50 text-blue-600"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-200 text-xs text-slate-500 bg-slate-50/70">
        <p className="font-semibold text-slate-700">Active Dataset</p>
        <p className="truncate text-slate-600 mt-0.5">{activeDataset || "Beijing PM2.5"}</p>
        <p className="mt-1 text-slate-400">RandomForestRegressor</p>
      </div>
    </aside>
  );
}
