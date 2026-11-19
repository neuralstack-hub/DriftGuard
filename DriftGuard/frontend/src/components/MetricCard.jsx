import React from "react";

export default function MetricCard({ title, value, subtitle, accent = "emerald" }) {
  const accentMap = {
    emerald: "text-emerald-400",
    amber: "text-amber-400",
    rose: "text-rose-400",
    sky: "text-sky-400",
    slate: "text-slate-100",
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</p>
      <p className={`mt-2 text-2xl font-bold ${accentMap[accent] || accentMap.slate}`}>{value}</p>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
}
