"use client";

import React, { useState } from "react";
import { formatINR, formatPct } from "@/lib/utils";
import { Layers, Search, ArrowUpRight } from "lucide-react";

interface Props {
  positions: any[];
}

export const PositionsView: React.FC<Props> = ({ positions }) => {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const filtered = (positions || []).filter((p) => {
    if (filter === "open" && !p.is_open) return false;
    if (filter === "closed" && p.is_open) return false;
    if (search && !p.symbol.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            Portfolio Positions
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            NSE Cash Equities (Long Only) — Live mark-to-market positions
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search symbol..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 w-48 font-mono"
            />
          </div>

          <div className="flex bg-slate-900 border border-slate-700 rounded-lg p-0.5 text-xs font-mono">
            {["all", "open", "closed"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded capitalize ${filter === f ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" : "text-slate-400 hover:text-white"}`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Symbol</th>
                <th className="py-3 px-4">Sector</th>
                <th className="py-3 px-4">Strategy</th>
                <th className="py-3 px-4 text-right">Quantity</th>
                <th className="py-3 px-4 text-right">Entry Price</th>
                <th className="py-3 px-4 text-right">Current Price</th>
                <th className="py-3 px-4 text-right">Unrealized P&L</th>
                <th className="py-3 px-4 text-right">Stop Loss</th>
                <th className="py-3 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((pos) => {
                const pnl = pos.unrealized_pnl || 0;
                const pnlPct = pos.average_entry_price > 0 ? (pos.current_price - pos.average_entry_price) / pos.average_entry_price : 0;
                return (
                  <tr key={pos.id} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-4 font-bold text-white flex items-center gap-1.5">
                      <span>{pos.symbol}</span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-cyan-400" />
                    </td>
                    <td className="py-3 px-4 text-slate-300">{pos.sector || "General"}</td>
                    <td className="py-3 px-4 text-cyan-400">{pos.strategy_key}</td>
                    <td className="py-3 px-4 text-right text-white font-semibold">{pos.quantity}</td>
                    <td className="py-3 px-4 text-right text-slate-300">{formatINR(pos.average_entry_price)}</td>
                    <td className="py-3 px-4 text-right text-white font-semibold">{formatINR(pos.current_price)}</td>
                    <td className="py-3 px-4 text-right">
                      <span className={`font-semibold ${pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {formatINR(pnl)} ({formatPct(pnlPct)})
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-rose-400">{pos.stop_loss ? formatINR(pos.stop_loss) : "None"}</td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] ${pos.is_open ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30" : "bg-slate-800 text-slate-400"}`}>
                        {pos.is_open ? "OPEN" : "CLOSED"}
                      </span>
                    </td>
                  </tr>
                );
              })}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No positions matching criteria.
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
