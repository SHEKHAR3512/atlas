"use client";

import React from "react";
import { ShieldAlert, AlertTriangle, AlertOctagon, CheckCircle2 } from "lucide-react";
import { TooltipInfo } from "@/components/TooltipInfo";

interface Props {
  riskData: any;
  onOpenKillModal: () => void;
}

export const RiskCenterView: React.FC<Props> = ({ riskData, onOpenKillModal }) => {
  const isKillActive = riskData?.kill_switch_active;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            Deterministic Risk Control Center
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Immutable capital preservation constraints & circuit breaker telemetry
          </p>
        </div>

        <button
          onClick={onOpenKillModal}
          className={`px-4 py-2 rounded-lg text-xs font-bold font-mono transition flex items-center gap-2 ${isKillActive ? "bg-rose-600 text-white animate-pulse" : "bg-rose-950 text-rose-300 border border-rose-600 hover:bg-rose-900"}`}
        >
          <AlertOctagon className="w-4 h-4" />
          <span>{isKillActive ? "KILL SWITCH IS ENGAGED" : "TRIGGER EMERGENCY KILL SWITCH"}</span>
        </button>
      </div>

      {/* Hard Risk Limit Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Gross Exposure Limit */}
        <div className="glass-panel p-5 rounded-xl border-slate-800">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-medium text-slate-300 flex items-center">
              Gross Portfolio Exposure <TooltipInfo term="Exposure" />
            </span>
            <span className="text-xs font-mono font-bold text-white">28.4% / 60.0% Max</span>
          </div>
          <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-800">
            <div className="bg-cyan-500 h-full rounded-full transition-all" style={{ width: `${(28.4 / 60) * 100}%` }} />
          </div>
          <div className="text-[11px] text-slate-400 mt-2 font-mono flex justify-between">
            <span>Buffer remaining: 31.6%</span>
            <span className="text-emerald-400">Within Safe Limits</span>
          </div>
        </div>

        {/* Daily Loss Limit */}
        <div className="glass-panel p-5 rounded-xl border-slate-800">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-medium text-slate-300 flex items-center">
              Daily Loss Usage <TooltipInfo term="Drawdown" />
            </span>
            <span className="text-xs font-mono font-bold text-white">0.32% / 1.50% Max</span>
          </div>
          <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-800">
            <div className="bg-emerald-500 h-full rounded-full transition-all" style={{ width: `${(0.32 / 1.5) * 100}%` }} />
          </div>
          <div className="text-[11px] text-slate-400 mt-2 font-mono flex justify-between">
            <span>Circuit trip threshold: -1.50%</span>
            <span className="text-emerald-400">Normal</span>
          </div>
        </div>

        {/* Weekly Loss Limit */}
        <div className="glass-panel p-5 rounded-xl border-slate-800">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-medium text-slate-300 flex items-center">
              Weekly Loss Usage
            </span>
            <span className="text-xs font-mono font-bold text-white">0.78% / 4.00% Max</span>
          </div>
          <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-800">
            <div className="bg-emerald-500 h-full rounded-full transition-all" style={{ width: `${(0.78 / 4.0) * 100}%` }} />
          </div>
          <div className="text-[11px] text-slate-400 mt-2 font-mono flex justify-between">
            <span>Weekly ceiling: 4.00%</span>
            <span className="text-emerald-400">Normal</span>
          </div>
        </div>

        {/* Portfolio Peak Drawdown */}
        <div className="glass-panel p-5 rounded-xl border-slate-800">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-medium text-slate-300 flex items-center">
              Portfolio Peak-to-Trough Drawdown
            </span>
            <span className="text-xs font-mono font-bold text-white">1.24% / 8.00% Max</span>
          </div>
          <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-800">
            <div className="bg-emerald-500 h-full rounded-full transition-all" style={{ width: `${(1.24 / 8.0) * 100}%` }} />
          </div>
          <div className="text-[11px] text-slate-400 mt-2 font-mono flex justify-between">
            <span>Hard liquidation stop: -8.00%</span>
            <span className="text-emerald-400">Safe</span>
          </div>
        </div>
      </div>

      {/* Sector Exposure Breakdown */}
      <div className="glass-panel p-5 rounded-xl border-slate-800">
        <h3 className="text-sm font-semibold text-white mb-4">
          Sector Concentration Telemetry (Max 15% per Sector)
        </h3>
        <div className="space-y-3 font-mono text-xs">
          {[
            { sector: "Technology", current: 9.8, max: 15.0 },
            { sector: "Energy", current: 8.5, max: 15.0 },
            { sector: "Financial Services", current: 6.2, max: 15.0 },
            { sector: "Consumer Goods", current: 3.9, max: 15.0 },
          ].map((sec) => (
            <div key={sec.sector} className="space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>{sec.sector}</span>
                <span className="font-semibold text-white">{sec.current}% / {sec.max}%</span>
              </div>
              <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-cyan-500 h-full rounded-full"
                  style={{ width: `${(sec.current / sec.max) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
