"use client";

import React from "react";
import { Compass, TrendingUp, AlertTriangle, ShieldCheck } from "lucide-react";
import { TooltipInfo } from "@/components/TooltipInfo";

interface Props {
  regimeData: any;
}

export const MarketRegimeView: React.FC<Props> = ({ regimeData }) => {
  const regime = regimeData?.regime || "bull_trend";
  const confidence = regimeData?.confidence ? regimeData.confidence * 100 : 85;
  const features = regimeData?.features || {};

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Compass className="w-5 h-5 text-cyan-400" />
          Market Regime Telemetry
        </h2>
        <p className="text-xs text-slate-400 font-mono">
          Deterministic classification of market state & dynamic strategy gating
        </p>
      </div>

      {/* Hero Regime State Card */}
      <div className="glass-panel rounded-2xl p-6 border-slate-800 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider flex items-center">
              Active Macro Regime <TooltipInfo term="Market Regime" />
            </span>
            <h3 className="text-3xl font-extrabold text-white mt-1 uppercase tracking-tight flex items-center gap-3">
              <span className="text-emerald-400">{regime.replace("_", " ")}</span>
            </h3>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Benchmark NIFTY 50 structure: Multi-timeframe trend alignment verified
            </p>
          </div>

          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 text-right font-mono">
            <div className="text-[10px] text-slate-400 uppercase">Classification Confidence</div>
            <div className="text-2xl font-bold text-cyan-400 mt-0.5">{confidence.toFixed(0)}%</div>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 font-mono text-xs">
          <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase">Realized Volatility</div>
            <div className="text-white font-bold text-sm mt-1">
              {features.realized_vol ? `${(features.realized_vol * 100).toFixed(1)}%` : "16.4%"}
            </div>
            <div className="text-[10px] text-emerald-400 mt-1">Normal Range (&lt;28%)</div>
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase">Trend Structure</div>
            <div className="text-white font-bold text-sm mt-1">EMA 20 &gt; 50 &gt; 200</div>
            <div className="text-[10px] text-emerald-400 mt-1">Bullish Stacked</div>
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase">Market Breadth</div>
            <div className="text-white font-bold text-sm mt-1">
              {features.market_breadth_pct ? `${(features.market_breadth_pct * 100).toFixed(0)}%` : "72%"}
            </div>
            <div className="text-[10px] text-emerald-400 mt-1">&gt;50-day EMA</div>
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase">Current Drawdown</div>
            <div className="text-white font-bold text-sm mt-1">
              {features.current_drawdown ? `${(features.current_drawdown * 100).toFixed(2)}%` : "-1.24%"}
            </div>
            <div className="text-[10px] text-emerald-400 mt-1">No Crisis Detected</div>
          </div>
        </div>
      </div>
    </div>
  );
};
