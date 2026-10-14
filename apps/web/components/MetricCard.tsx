"use client";

import React from "react";
import { TooltipInfo } from "./TooltipInfo";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: string;
  isPositive?: boolean;
  tooltipTerm?: string;
  icon?: React.ReactNode;
  variant?: "default" | "cyan" | "emerald" | "amber" | "rose";
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  change,
  isPositive,
  tooltipTerm,
  icon,
  variant = "default",
}) => {
  const borderVariants = {
    default: "border-slate-800/80 hover:border-slate-700",
    cyan: "border-cyan-500/30 hover:border-cyan-500/50 glow-cyan",
    emerald: "border-emerald-500/30 hover:border-emerald-500/50 glow-emerald",
    amber: "border-amber-500/30 hover:border-amber-500/50",
    rose: "border-rose-500/30 hover:border-rose-500/50 glow-rose",
  };

  return (
    <div
      className={cn(
        "glass-panel rounded-xl p-4 transition-all duration-200 relative overflow-hidden",
        borderVariants[variant]
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center text-xs font-medium text-slate-400">
          <span>{title}</span>
          {tooltipTerm && <TooltipInfo term={tooltipTerm} />}
        </div>
        {icon && <div className="text-slate-400 opacity-80">{icon}</div>}
      </div>

      <div className="flex items-baseline justify-between">
        <div className="text-2xl font-bold tracking-tight text-white font-mono">
          {value}
        </div>
        {change && (
          <span
            className={cn(
              "text-xs font-mono font-medium px-1.5 py-0.5 rounded",
              isPositive
                ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30"
                : "bg-rose-950/60 text-rose-400 border border-rose-500/30"
            )}
          >
            {change}
          </span>
        )}
      </div>

      {subtitle && (
        <div className="text-[11px] text-slate-400 mt-1 font-mono">{subtitle}</div>
      )}
    </div>
  );
};
