"use client";

import React, { useState } from "react";
import { formatINR } from "@/lib/utils";
import { ArrowLeftRight, CheckCircle2, Clock, XCircle } from "lucide-react";

interface Props {
  orders: any[];
}

export const OrdersView: React.FC<Props> = ({ orders }) => {
  const [filter, setFilter] = useState("all");

  const filtered = (orders || []).filter((o) => {
    if (filter === "filled" && o.status !== "FILLED") return false;
    if (filter === "pending" && o.status !== "SUBMITTED" && o.status !== "PENDING") return false;
    if (filter === "rejected" && o.status !== "REJECTED" && o.status !== "CANCELLED") return false;
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "FILLED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-emerald-950/60 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" /> FILLED
          </span>
        );
      case "SUBMITTED":
      case "PENDING":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-amber-950/60 text-amber-400 border border-amber-500/30">
            <Clock className="w-3 h-3" /> PENDING
          </span>
        );
      case "REJECTED":
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-rose-950/60 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3 h-3" /> {status}
          </span>
        );
      default:
        return <span className="text-slate-400">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ArrowLeftRight className="w-5 h-5 text-cyan-400" />
            Order Execution Book
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Idempotent client order audit trail & fills
          </p>
        </div>

        <div className="flex bg-slate-900 border border-slate-700 rounded-lg p-0.5 text-xs font-mono">
          {["all", "filled", "pending", "rejected"].map((f) => (
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

      <div className="glass-panel rounded-xl overflow-hidden border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Client Order ID</th>
                <th className="py-3 px-4">Symbol</th>
                <th className="py-3 px-4">Side</th>
                <th className="py-3 px-4 text-right">Quantity</th>
                <th className="py-3 px-4 text-right">Limit Price</th>
                <th className="py-3 px-4 text-right">Fill Price</th>
                <th className="py-3 px-4">Strategy</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((ord) => (
                <tr key={ord.id} className="hover:bg-slate-900/40 transition">
                  <td className="py-3 px-4 text-slate-400 text-[11px] truncate max-w-[180px]">
                    {ord.client_order_id}
                  </td>
                  <td className="py-3 px-4 font-bold text-white">{ord.symbol}</td>
                  <td className="py-3 px-4">
                    <span className={`font-semibold ${ord.side === "BUY" ? "text-cyan-400" : "text-amber-400"}`}>
                      {ord.side}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-white font-semibold">{ord.quantity}</td>
                  <td className="py-3 px-4 text-right text-slate-300">{formatINR(ord.price)}</td>
                  <td className="py-3 px-4 text-right text-white font-semibold">
                    {ord.average_fill_price ? formatINR(ord.average_fill_price) : "—"}
                  </td>
                  <td className="py-3 px-4 text-cyan-400 text-[11px]">{ord.strategy_key}</td>
                  <td className="py-3 px-4 text-center">{getStatusBadge(ord.status)}</td>
                  <td className="py-3 px-4 text-right text-slate-400 text-[11px]">
                    {ord.submitted_at ? new Date(ord.submitted_at).toLocaleTimeString() : "—"}
                  </td>
                </tr>
              ))}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No orders recorded yet.
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
