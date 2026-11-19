import React from "react";

export default function MetricCard({ title, value, subtitle, accent = "blue" }) {
  const accentMap = {
    blue: "text-blue-600",
    emerald: "text-emerald-600",
    amber: "text-amber-600",
    rose: "text-rose-600",
    sky: "text-blue-600",
    slate: "text-slate-900",
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</p>
      <p className={`mt-2 text-2xl font-bold ${accentMap[accent] || accentMap.slate}`}>{value}</p>
      {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
}
