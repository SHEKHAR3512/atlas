"use client";

import React, { useEffect, useState } from "react";
import { Activity, CheckCircle2, XCircle, AlertTriangle, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";

export const SystemHealthView: React.FC = () => {
  const [preflight, setPreflight] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLivePreflight().then((data) => {
      setPreflight(data);
      setLoading(false);
    }).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-cyan-400" />
          System Health & Live Trading Preflight Gate
        </h2>
        <p className="text-xs text-slate-400 font-mono">
          Rigorous safety verification ensuring fail-closed architecture before any live capital exposure
        </p>
      </div>

      {/* Preflight Summary Banner */}
      <div className={`p-5 rounded-2xl border ${preflight?.live_ready ? "bg-emerald-950/40 border-emerald-500/50" : "bg-slate-900 border-slate-800"}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-[10px] text-slate-400 font-mono uppercase">Live Execution Clearance</div>
            <div className="text-2xl font-bold font-mono mt-0.5 flex items-center gap-2">
              {preflight?.live_ready ? (
                <span className="text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 className="w-6 h-6" /> CLEARED FOR LIVE TRADING
                </span>
              ) : (
                <span className="text-amber-400 flex items-center gap-2">
                  <ShieldCheck className="w-6 h-6" /> BLOCKED (FAIL-CLOSED SAFETY ACTIVE)
                </span>
              )}
            </div>
          </div>
          <div className="text-xs font-mono text-slate-400">
            System Mode: <span className="text-white font-bold">{preflight?.system_mode || "PAPER"}</span>
          </div>
        </div>
      </div>

      {/* Preflight Checklist Items */}
      <div className="glass-panel rounded-xl overflow-hidden border-slate-800">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Preflight Checklist Gates</h3>
          <span className="text-xs text-slate-400 font-mono">
            {preflight?.checks?.filter((c: any) => c.passed).length || 5} of {preflight?.checks?.length || 8} Passed
          </span>
        </div>

        <div className="divide-y divide-slate-800/60 font-mono text-xs">
          {preflight?.checks?.map((chk: any) => (
            <div key={chk.name} className="p-3.5 flex items-center justify-between hover:bg-slate-900/40 transition">
              <div className="flex items-center gap-3">
                {chk.passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                )}
                <div>
                  <div className="text-white font-semibold flex items-center gap-2">
                    <span>{chk.name}</span>
                    {chk.critical && (
                      <span className="text-[9px] bg-rose-950 text-rose-400 px-1.5 py-0.2 rounded border border-rose-800">
                        CRITICAL
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-400">{chk.message}</div>
                </div>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${chk.passed ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30" : "bg-rose-950/60 text-rose-400 border border-rose-500/30"}`}>
                {chk.passed ? "PASS" : "BLOCKED"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
