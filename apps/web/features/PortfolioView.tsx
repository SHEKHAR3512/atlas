"use client";

import React from "react";
import { PieChart, ResponsiveContainer, Pie, Cell, Tooltip } from "recharts";
import { formatINR } from "@/lib/utils";

interface Props {
  portfolio: any;
  positions: any[];
}

export const PortfolioView: React.FC<Props> = ({ portfolio, positions }) => {
  const cash = portfolio?.cash || 71600;
  const equity = portfolio?.equity || 100000;
  const invested = equity - cash;

  const allocationData = [
    { name: "Liquid Cash", value: cash, color: "#06b6d4" },
    { name: "Active Equities", value: invested > 0 ? invested : 28400, color: "#10b981" },
  ];

  const sectorData = [
    { name: "Technology", value: 38, color: "#6366f1" },
    { name: "Energy", value: 32, color: "#06b6d4" },
    { name: "Financial Services", value: 20, color: "#10b981" },
    { name: "Consumer Goods", value: 10, color: "#f59e0b" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white">Portfolio Asset Allocation</h2>
        <p className="text-xs text-slate-400 font-mono">
          Capital breakdown, cash buffers, and sector diversification
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Cash vs Equity Allocation */}
        <div className="glass-panel p-5 rounded-xl border-slate-800">
          <h3 className="text-sm font-semibold text-white mb-3">Asset Allocation (Cash vs Invested)</h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={allocationData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {allocationData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: any) => formatINR(val)}
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-6 text-xs font-mono">
            {allocationData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-slate-300">{item.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Sector Concentration */}
        <div className="glass-panel p-5 rounded-xl border-slate-800">
          <h3 className="text-sm font-semibold text-white mb-3">Sector Weight Distribution</h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sectorData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {sectorData.map((entry, index) => (
                    <Cell key={`cell-sec-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: any) => `${val}%`}
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center flex-wrap gap-4 text-xs font-mono">
            {sectorData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-slate-300">{item.name} ({item.value}%)</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
