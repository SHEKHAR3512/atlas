"use client";

import React from "react";
import { ShieldCheck, AlertTriangle } from "lucide-react";

interface Props {
  isLive?: boolean;
}

export const PaperTradingBanner: React.FC<Props> = ({ isLive = false }) => {
  if (isLive) {
    return (
      <div className="bg-rose-950/80 border-b border-rose-500/50 px-4 py-2 text-rose-200 text-xs font-mono flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 animate-pulse" />
          <span className="font-bold tracking-wider">LIVE TRADING ACTIVE — REAL CAPITAL AT RISK</span>
        </div>
        <span className="bg-rose-900/60 text-rose-300 px-2 py-0.5 rounded border border-rose-600/40 text-[10px]">
          REAL MONEY
        </span>
      </div>
    );
  }

  return (
    <div className="bg-cyan-950/40 border-b border-cyan-500/20 px-4 py-1.5 text-cyan-200 text-xs font-mono flex items-center justify-between">
      <div className="flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 text-cyan-400" />
        <span className="font-semibold tracking-wide">PAPER TRADING SIMULATION</span>
        <span className="text-slate-400">— NO REAL MONEY AT RISK</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="bg-emerald-950/60 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30 text-[10px]">
          SAFE MODE
        </span>
        <span className="text-slate-400 text-[11px]">NSE CASH (LONG ONLY)</span>
      </div>
    </div>
  );
};
