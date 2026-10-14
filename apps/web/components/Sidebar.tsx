"use client";

import React from "react";
import {
  LayoutDashboard,
  PieChart,
  Layers,
  ArrowLeftRight,
  TrendingUp,
  FlaskConical,
  History,
  ShieldAlert,
  Compass,
  FileQuestion,
  Activity,
  ScrollText,
  AlertOctagon,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type NavTab =
  | "overview"
  | "portfolio"
  | "positions"
  | "orders"
  | "strategies"
  | "research"
  | "backtests"
  | "risk"
  | "regime"
  | "explain"
  | "health"
  | "audit";

interface SidebarProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  killSwitchActive: boolean;
  onOpenKillModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  killSwitchActive,
  onOpenKillModal,
}) => {
  const navItems = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "portfolio", label: "Portfolio", icon: PieChart },
    { id: "positions", label: "Positions", icon: Layers },
    { id: "orders", label: "Orders", icon: ArrowLeftRight },
    { id: "strategies", label: "Strategies", icon: TrendingUp },
    { id: "research", label: "Research Lab", icon: FlaskConical },
    { id: "backtests", label: "Backtests", icon: History },
    { id: "risk", label: "Risk Center", icon: ShieldAlert },
    { id: "regime", label: "Market Regime", icon: Compass },
    { id: "explain", label: "Explainability", icon: FileQuestion },
    { id: "health", label: "System Health", icon: Activity },
    { id: "audit", label: "Audit Trail", icon: ScrollText },
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950/70 flex flex-col justify-between p-4 shrink-0 min-h-screen">
      <div>
        {/* Brand */}
        <div className="flex items-center gap-3 px-2 py-3 mb-6">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/20">
            A
          </div>
          <div>
            <div className="font-bold tracking-wider text-white text-base">ATLAS</div>
            <div className="text-[10px] text-cyan-400 font-mono">AUTONOMOUS QUANT V1</div>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id as NavTab)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150",
                  active
                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                )}
              >
                <Icon className={cn("w-4 h-4", active ? "text-cyan-400" : "text-slate-500")} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Emergency Hard Kill Switch Button */}
      <div className="pt-4 border-t border-slate-800/80">
        <button
          onClick={onOpenKillModal}
          className={cn(
            "w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-xs font-mono font-bold transition-all",
            killSwitchActive
              ? "bg-rose-600 text-white animate-pulse shadow-lg shadow-rose-600/30"
              : "bg-rose-950/60 text-rose-300 border border-rose-700/50 hover:bg-rose-900/80 hover:text-white"
          )}
        >
          <AlertOctagon className="w-4 h-4" />
          <span>{killSwitchActive ? "KILL SWITCH ENGAGED" : "TRIGGER KILL SWITCH"}</span>
        </button>
        <div className="text-[10px] text-center text-slate-500 mt-2 font-mono">
          FAIL-CLOSED ARMED
        </div>
      </div>
    </aside>
  );
};
