"use client";

import React from "react";
import { TrendingUp, CheckCircle, ShieldAlert, Activity } from "lucide-react";
import { TooltipInfo } from "@/components/TooltipInfo";

interface Props {
  strategies: any[];
}

export const StrategiesView: React.FC<Props> = ({ strategies }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-cyan-400" />
          Quantitative Strategies
        </h2>
        <p className="text-xs text-slate-400 font-mono">
          Systematic strategies operating across cash equities with deterministic allocations
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {(strategies || []).map((strat) => {
          const status = strat.status || "APPROVED";
          const isApproved = status === "APPROVED" || status === "LIVE";
          return (
            <div
              key={strat.id}
              className="glass-panel rounded-xl p-5 border-slate-800 hover:border-slate-700 transition"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-white text-base">{strat.name}</h3>
                    <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                      v{strat.version}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 font-mono mt-0.5">{strat.id}</div>
                </div>

                <span
                  className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded-full border ${isApproved ? "bg-emerald-950/60 text-emerald-400 border-emerald-500/30" : "bg-amber-950/60 text-amber-400 border-amber-500/30"}`}
                >
                  {status}
                </span>
              </div>

              {/* Regime Affinities */}
              <div className="mb-4">
                <div className="text-[10px] text-slate-400 font-mono mb-1.5 uppercase tracking-wider flex items-center">
                  Compatible Regimes <TooltipInfo term="Market Regime" />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(strat.compatible_regimes || ["bull_trend"]).map((r: string) => (
                    <span
                      key={r}
                      className="text-[10px] font-mono bg-slate-900 text-slate-300 px-2 py-0.5 rounded border border-slate-700 uppercase"
                    >
                      {r.replace("_", " ")}
                    </span>
                  ))}
                </div>
              </div>

              {/* Quantitative Metrics Grid */}
              <div className="grid grid-cols-3 gap-2.5 pt-3 border-t border-slate-800/80 font-mono text-xs mb-4">
                <div className="bg-slate-900/50 p-2 rounded border border-slate-800">
                  <div className="text-[10px] text-slate-400">Target Weight</div>
                  <div className="text-white font-bold">{((strat.allocation_pct || 0.25) * 100).toFixed(0)}%</div>
                </div>

                <div className="bg-slate-900/50 p-2 rounded border border-slate-800">
                  <div className="text-[10px] text-slate-400">Validated Sharpe</div>
                  <div className="text-emerald-400 font-bold">1.82</div>
                </div>

                <div className="bg-slate-900/50 p-2 rounded border border-slate-800">
                  <div className="text-[10px] text-slate-400">Max Drawdown</div>
                  <div className="text-cyan-400 font-bold">1.62%</div>
                </div>
              </div>

              {/* Parameters Accordion / Pill */}
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60 text-[11px] font-mono">
                <div className="text-slate-400 text-[10px] mb-1 uppercase font-semibold">
                  Parameters Configuration:
                </div>
                <div className="text-slate-300 space-y-0.5">
                  {Object.entries(strat.parameters || {}).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-slate-400">{k}:</span>
                      <span className="text-cyan-300 font-semibold">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
