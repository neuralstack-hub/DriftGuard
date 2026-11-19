import React from "react";

const STYLES = {
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  promoted: "bg-emerald-50 text-emerald-700 border-emerald-200",
  STABLE: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Healthy: "bg-emerald-50 text-emerald-700 border-emerald-200",
  dispatched: "bg-emerald-50 text-emerald-700 border-emerald-200",
  archived: "bg-slate-100 text-slate-600 border-slate-200",
  "No Model": "bg-slate-100 text-slate-600 border-slate-200",
  candidate: "bg-blue-50 text-blue-700 border-blue-200",
  rejected: "bg-rose-50 text-rose-700 border-rose-200",
  Critical: "bg-rose-50 text-rose-700 border-rose-200",
  "DRIFT DETECTED": "bg-rose-50 text-rose-700 border-rose-200",
  Warning: "bg-amber-50 text-amber-700 border-amber-200",
  skipped_unconfigured: "bg-amber-50 text-amber-700 border-amber-200",
};

export default function StatusBadge({ status }) {
  const cls = STYLES[status] || "bg-slate-100 text-slate-600 border-slate-200";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {status}
    </span>
  );
}
