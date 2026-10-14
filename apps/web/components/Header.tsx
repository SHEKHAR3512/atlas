"use client";

import React from "react";
import { RefreshCw, ShieldAlert, Clock, Circle } from "lucide-react";
import { NavTab } from "./Sidebar";

interface HeaderProps {
  currentTab: NavTab;
  onRefresh: () => void;
  isRefreshing: boolean;
  killSwitchActive: boolean;
  onOpenKillModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onRefresh,
  isRefreshing,
  killSwitchActive,
  onOpenKillModal,
}) => {
  const titles: Record<NavTab, string> = {
    overview: "Autonomous Trading Ecosystem Overview",
    portfolio: "Portfolio & Asset Allocation",
    positions: "Cash Equities Positions",
    orders: "Order Management & Idempotency",
    strategies: "Systematic Quantitative Strategies",
    research: "Autonomous Research Lab & Candidate Pipeline",
    backtests: "Strategy Backtesting & Walk-Forward",
    risk: "Deterministic Risk Engine & Limits",
    regime: "Macro Market Regime Detection",
    explain: "Verifiable Trade Explainability",
    health: "System Health & Live Preflight",
    audit: "Immutable Audit Trail",
  };

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/40 backdrop-blur px-6 flex items-center justify-between shrink-0">
      <div>
        <h1 className="text-base font-bold text-white capitalize">{titles[currentTab]}</h1>
        <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
          <Clock className="w-3 h-3 text-cyan-400" />
          <span>NSE CASH SESSION (09:15 - 15:30 IST)</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Status indicator */}
        <div className="hidden sm:flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono">
          <Circle className="w-2.5 h-2.5 fill-emerald-400 text-emerald-400 animate-pulse" />
          <span className="text-slate-300">AUTO-PILOT ACTIVE</span>
        </div>

        {/* Refresh button */}
        <button
          onClick={onRefresh}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
          title="Refresh telemetry data"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-cyan-400" : ""}`} />
        </button>

        {/* Kill Switch Quick Badge */}
        <button
          onClick={onOpenKillModal}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition border ${killSwitchActive ? "bg-rose-950 text-rose-300 border-rose-600 animate-pulse" : "bg-slate-900 text-emerald-400 border-emerald-500/30"}`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>{killSwitchActive ? "HALT" : "NORMAL"}</span>
        </button>
      </div>
    </header>
  );
};
