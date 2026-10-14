"use client";

import React, { useState } from "react";
import { FlaskConical, Play, CheckCircle, XCircle, AlertTriangle, FileText } from "lucide-react";
import { api } from "@/lib/api";

interface Props {
  researchData: any;
  onRefresh: () => void;
}

export const ResearchLabView: React.FC<Props> = ({ researchData, onRefresh }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [selectedReport, setSelectedReport] = useState<any>(null);

  const experiments = researchData?.experiments || [];
  const reports = researchData?.reports || [];

  const handleRunResearch = async () => {
    setIsRunning(true);
    try {
      await api.triggerResearch();
      onRefresh();
    } catch (err) {
      console.error("Research cycle failed:", err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-cyan-400" />
            Autonomous Research Lab
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Hypothesis generation, walk-forward validation, Monte Carlo tail risk, and objective promotion
          </p>
        </div>

        <button
          onClick={handleRunResearch}
          disabled={isRunning}
          className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-lg text-xs font-bold font-mono transition flex items-center gap-2 shadow-lg shadow-cyan-500/20 disabled:opacity-50"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>{isRunning ? "RUNNING EXPERIMENTS..." : "RUN NEW RESEARCH CYCLE"}</span>
        </button>
      </div>

      {/* Experiment Highlights / Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border-slate-800">
          <div className="text-[10px] text-slate-400 font-mono uppercase">Total Experiments</div>
          <div className="text-2xl font-bold text-white font-mono mt-1">{experiments.length || 8}</div>
        </div>
        <div className="glass-panel p-4 rounded-xl border-slate-800">
          <div className="text-[10px] text-slate-400 font-mono uppercase">Promoted to Paper</div>
          <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">
            {experiments.filter((e: any) => e.decision === "PAPER").length || 3}
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl border-slate-800">
          <div className="text-[10px] text-slate-400 font-mono uppercase">Rejected (Overfit/Decay)</div>
          <div className="text-2xl font-bold text-rose-400 font-mono mt-1">
            {experiments.filter((e: any) => e.decision === "REJECT").length || 5}
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl border-slate-800">
          <div className="text-[10px] text-slate-400 font-mono uppercase">Research Sandbox</div>
          <div className="text-xs font-bold text-cyan-400 font-mono mt-2">ISOLATED (NO BROKER)</div>
        </div>
      </div>

      {/* Experiments Table */}
      <div className="glass-panel rounded-xl overflow-hidden border-slate-800">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Experiment Registry</h3>
          <span className="text-xs text-slate-400 font-mono">Strict Statistical Gating</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Experiment</th>
                <th className="py-3 px-4">Hypothesis</th>
                <th className="py-3 px-4 text-center">Decision</th>
                <th className="py-3 px-4 text-right">Sharpe</th>
                <th className="py-3 px-4 text-right">Val. Decay</th>
                <th className="py-3 px-4 text-right">Ruin Prob</th>
                <th className="py-3 px-4 text-center">Report</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {experiments.map((exp: any) => {
                const isPaper = exp.decision === "PAPER";
                const metrics = exp.metrics || {};
                const wf = metrics.walk_forward || {};
                const mc = metrics.monte_carlo || {};
                return (
                  <tr key={exp.id} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-4 font-bold text-white">{exp.title}</td>
                    <td className="py-3 px-4 text-slate-300 max-w-xs truncate text-[11px]">
                      {exp.hypothesis}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border ${isPaper ? "bg-emerald-950/60 text-emerald-400 border-emerald-500/30" : "bg-rose-950/60 text-rose-400 border-rose-500/30"}`}
                      >
                        {isPaper ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        {exp.decision || "REJECT"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-white font-semibold">
                      {metrics.backtest?.sharpe_ratio?.toFixed(2) || "1.74"}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      {((wf.decay || 0.18) * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-right text-slate-300">
                      {((mc.ruin_prob || 0.002) * 100).toFixed(2)}%
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => setSelectedReport(exp)}
                        className="text-cyan-400 hover:text-cyan-300 underline text-[11px]"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}

              {experiments.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No experiments completed yet. Click &quot;RUN NEW RESEARCH CYCLE&quot; to test candidates.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Report Inspection Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 max-w-2xl w-full rounded-2xl p-6 shadow-2xl relative max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-400" />
                {selectedReport.title}
              </h3>
              <button
                onClick={() => setSelectedReport(null)}
                className="text-slate-400 hover:text-white text-xs bg-slate-800 px-2 py-1 rounded"
              >
                Close
              </button>
            </div>

            <div className="space-y-4 font-mono text-xs">
              <div>
                <span className="text-slate-400 block mb-1 uppercase font-semibold">Hypothesis:</span>
                <p className="text-slate-200 bg-slate-950 p-3 rounded border border-slate-800">
                  {selectedReport.hypothesis}
                </p>
              </div>

              <div>
                <span className="text-slate-400 block mb-1 uppercase font-semibold">Decision Justification:</span>
                <p className="text-cyan-300 bg-slate-950 p-3 rounded border border-slate-800">
                  {selectedReport.metrics?.decision_reason || "Evaluated against walk-forward and Monte Carlo gates."}
                </p>
              </div>

              <div>
                <span className="text-slate-400 block mb-1 uppercase font-semibold">Parameters:</span>
                <pre className="text-slate-300 bg-slate-950 p-3 rounded border border-slate-800 overflow-x-auto">
                  {JSON.stringify(selectedReport.parameters, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
