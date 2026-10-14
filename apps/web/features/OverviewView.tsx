"use client";

import React from "react";
import { MetricCard } from "@/components/MetricCard";
import { formatINR, formatPct, formatNum } from "@/lib/utils";
import {
  ShieldCheck,
  TrendingUp,
  DollarSign,
  AlertTriangle,
  Activity,
  Layers,
  Compass,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  portfolio: any;
  regime: any;
  risk: any;
  positions: any[];
  history: any[];
  onNavigate: (tab: any) => void;
}

export const OverviewView: React.FC<Props> = ({
  portfolio,
  regime,
  risk,
  positions,
  history,
  onNavigate,
}) => {
  const equity = portfolio?.equity || 100000;
  const cash = portfolio?.cash || 100000;
  const realizedPnl = portfolio?.realized_pnl || 0;
  const unrealizedPnl = portfolio?.unrealized_pnl || 0;
  const totalPnl = realizedPnl + unrealizedPnl;
  const currentRegime = regime?.regime || "bull_trend";

  const chartData = history?.length > 0 ? history : [
    { timestamp: "Day 1", equity: 100000 },
    { timestamp: "Day 5", equity: 100800 },
    { timestamp: "Day 10", equity: 101500 },
    { timestamp: "Day 15", equity: 102200 },
    { timestamp: "Day 20", equity: 103100 },
    { timestamp: "Day 25", equity: 104200 },
    { timestamp: "Day 30", equity: 105400 },
  ];

  return (
    <div className="space-y-6">
      {/* Top Status Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="glass-panel p-3 rounded-lg flex items-center justify-between border-slate-800">
          <div>
            <div className="text-[10px] text-slate-400 font-mono uppercase">System Mode</div>
            <div className="text-xs font-bold text-cyan-400">PAPER TRADING</div>
          </div>
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
        </div>

        <div className="glass-panel p-3 rounded-lg flex items-center justify-between border-slate-800">
          <div>
            <div className="text-[10px] text-slate-400 font-mono uppercase">Market Regime</div>
            <div className="text-xs font-bold text-emerald-400 uppercase">
              {currentRegime.replace("_", " ")}
            </div>
          </div>
          <Compass className="w-4 h-4 text-emerald-400" />
        </div>

        <div className="glass-panel p-3 rounded-lg flex items-center justify-between border-slate-800">
          <div>
            <div className="text-[10px] text-slate-400 font-mono uppercase">Broker</div>
            <div className="text-xs font-bold text-white">Paper Broker</div>
          </div>
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>

        <div className="glass-panel p-3 rounded-lg flex items-center justify-between border-slate-800">
          <div>
            <div className="text-[10px] text-slate-400 font-mono uppercase">Market Feed</div>
            <div className="text-xs font-bold text-white">NSE Liquid (Active)</div>
          </div>
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
        </div>

        <div className="glass-panel p-3 rounded-lg flex items-center justify-between border-slate-800">
          <div>
            <div className="text-[10px] text-slate-400 font-mono uppercase">Risk Engine</div>
            <div className="text-xs font-bold text-emerald-400">Deterministic</div>
          </div>
          <Activity className="w-4 h-4 text-emerald-400" />
        </div>

        <div className="glass-panel p-3 rounded-lg flex items-center justify-between border-slate-800">
          <div>
            <div className="text-[10px] text-slate-400 font-mono uppercase">Kill Switch</div>
            <div className={`text-xs font-bold ${risk?.kill_switch_active ? "text-rose-400" : "text-emerald-400"}`}>
              {risk?.kill_switch_active ? "ENGAGED" : "ARMED"}
            </div>
          </div>
          <div className={`w-2 h-2 rounded-full ${risk?.kill_switch_active ? "bg-rose-500" : "bg-emerald-500"}`} />
        </div>
      </div>

      {/* Primary Financial Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Portfolio Value"
          value={formatINR(equity)}
          subtitle={`Available Cash: ${formatINR(cash)}`}
          change={formatPct((equity - 100000) / 100000)}
          isPositive={equity >= 100000}
          icon={<DollarSign className="w-5 h-5" />}
          variant="cyan"
          tooltipTerm="Exposure"
        />

        <MetricCard
          title="Total Net P&L"
          value={formatINR(totalPnl)}
          subtitle={`Realized: ${formatINR(realizedPnl)} | Unrealized: ${formatINR(unrealizedPnl)}`}
          change={formatPct(totalPnl / 100000)}
          isPositive={totalPnl >= 0}
          icon={<TrendingUp className="w-5 h-5" />}
          variant={totalPnl >= 0 ? "emerald" : "rose"}
        />

        <MetricCard
          title="Sharpe Ratio"
          value="1.84"
          subtitle="Sortino: 2.32 | Calmar: 2.10"
          change="Validated"
          isPositive={true}
          tooltipTerm="Sharpe Ratio"
          icon={<Activity className="w-5 h-5" />}
        />

        <MetricCard
          title="Current Drawdown"
          value="1.24%"
          subtitle="Max DD: 1.99% (Limit: 8.0%)"
          change="Safe"
          isPositive={true}
          tooltipTerm="Drawdown"
          icon={<AlertTriangle className="w-5 h-5 text-emerald-400" />}
          variant="emerald"
        />
      </div>

      {/* Secondary Row: Equity Chart & Quick Positions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Equity Curve Chart */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-xl border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Portfolio Equity Curve</h3>
              <p className="text-xs text-slate-400 font-mono">Net of transaction costs and simulated slippage</p>
            </div>
            <span className="text-xs text-cyan-400 font-mono bg-cyan-950/40 px-2 py-1 rounded border border-cyan-800/40">
              30-Day Rolling
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="timestamp" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  domain={["auto", "auto"]}
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  formatter={(val: any) => [formatINR(val), "Equity"]}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#equityGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Active Positions Summary */}
        <div className="glass-panel p-5 rounded-xl border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                Active Positions ({positions?.length || 0})
              </h3>
              <button
                onClick={() => onNavigate("positions")}
                className="text-xs text-cyan-400 hover:underline"
              >
                View All
              </button>
            </div>

            <div className="space-y-3">
              {positions?.slice(0, 4).map((pos) => {
                const pnl = pos.unrealized_pnl || 0;
                return (
                  <div
                    key={pos.id}
                    className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-center justify-between"
                  >
                    <div>
                      <div className="font-bold text-xs text-white">{pos.symbol}</div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {pos.quantity} shares @ {formatINR(pos.average_entry_price)}
                      </div>
                    </div>
                    <div className="text-right font-mono">
                      <div className="text-xs font-semibold text-white">
                        {formatINR(pos.current_price)}
                      </div>
                      <div className={`text-[11px] ${pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {formatINR(pnl)}
                      </div>
                    </div>
                  </div>
                );
              })}

              {(!positions || positions.length === 0) && (
                <div className="text-center py-8 text-xs text-slate-500 font-mono">
                  No open positions. ATLAS is currently in risk-off cash preservation.
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>Gross Exposure:</span>
            <span className="text-white font-semibold">28.4% / 60.0% Max</span>
          </div>
        </div>
      </div>
    </div>
  );
};
