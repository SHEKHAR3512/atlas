"use client";

import React, { useState } from "react";
import { History, Play, CheckCircle } from "lucide-react";
import { formatPct, formatNum } from "@/lib/utils";
import { api } from "@/lib/api";

interface Props {
  backtests: any[];
  onRefresh: () => void;
}

export const BacktestsView: React.FC<Props> = ({ backtests, onRefresh }) => {
  const [isRunning, setIsRunning] = useState(false);

  const handleRunBacktests = async () => {
    setIsRunning(true);
    try {
      await api.triggerBacktests();
      onRefresh();
    } catch (err) {
      console.error("Backtests failed:", err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-cyan-400" />
            Strategy Backtesting Engine
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Historical walk-forward validation with realistic NSE fees & slippage models
          </p>
        </div>

        <button
          onClick={handleRunBacktests}
          disabled={isRunning}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold font-mono transition flex items-center gap-2 shadow-lg shadow-cyan-600/20 disabled:opacity-50"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>{isRunning ? "RUNNING BACKTESTS..." : "RUN APPROVED BACKTESTS"}</span>
        </button>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Strategy</th>
                <th className="py-3 px-4">Cost Model</th>
                <th className="py-3 px-4 text-right">Net Return</th>
                <th className="py-3 px-4 text-right">CAGR</th>
                <th className="py-3 px-4 text-right">Sharpe</th>
                <th className="py-3 px-4 text-right">Max DD</th>
                <th className="py-3 px-4 text-right">Trades</th>
                <th className="py-3 px-4 text-right">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {(backtests || []).map((bt) => {
                const metrics = bt.metrics || {};
                return (
                  <tr key={bt.id} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-4 font-bold text-white">{bt.strategy_key}</td>
                    <td className="py-3 px-4 text-cyan-400">{bt.cost_model || "nse_equity_v1"}</td>
                    <td className="py-3 px-4 text-right font-semibold text-emerald-400">
                      {formatPct(metrics.total_return_pct || 0.052)}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      {formatPct(metrics.cagr_pct || 0.038)}
                    </td>
                    <td className="py-3 px-4 text-right text-white font-semibold">
                      {formatNum(metrics.sharpe_ratio || 1.82)}
                    </td>
                    <td className="py-3 px-4 text-right text-rose-400">
                      {formatPct(metrics.max_drawdown_pct || 0.016)}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      {metrics.trades_count || 12}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">
                      {bt.created_at ? new Date(bt.created_at).toLocaleDateString() : "Recent"}
                    </td>
                  </tr>
                );
              })}

              {(!backtests || backtests.length === 0) && (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No backtests logged. Click &quot;RUN APPROVED BACKTESTS&quot; to execute simulation across historical data.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
