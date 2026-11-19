import React from "react";

const STYLES = {
  active: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  promoted: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  STABLE: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  dispatched: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  archived: "bg-slate-700/40 text-slate-300 border-slate-600/40",
  candidate: "bg-sky-500/15 text-sky-400 border-sky-500/30",
  rejected: "bg-rose-500/15 text-rose-400 border-rose-500/30",
  "DRIFT DETECTED": "bg-rose-500/15 text-rose-400 border-rose-500/30",
  skipped_unconfigured: "bg-amber-500/15 text-amber-400 border-amber-500/30",
};

export default function StatusBadge({ status }) {
  const cls = STYLES[status] || "bg-slate-700/40 text-slate-300 border-slate-600/40";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {status}
    </span>
  );
}
