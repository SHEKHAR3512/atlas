"use client";

import React, { useState } from "react";
import { ScrollText, Search, Code2 } from "lucide-react";

interface Props {
  auditLogs: any[];
}

export const AuditLogView: React.FC<Props> = ({ auditLogs }) => {
  const [filterType, setFilterType] = useState("all");
  const [selectedEntry, setSelectedEntry] = useState<any>(null);

  const eventTypes = ["all", "SIGNAL", "RISK_DECISION", "ORDER_FILLED", "KILL_SWITCH", "PROPOSAL"];

  const filtered = (auditLogs || []).filter((log) => {
    if (filterType !== "all" && log.event_type !== filterType) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ScrollText className="w-5 h-5 text-cyan-400" />
            Immutable Audit Trail
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Cryptographically traceable chronological ledger of all trading decisions
          </p>
        </div>

        <div className="flex flex-wrap bg-slate-900 border border-slate-700 rounded-lg p-0.5 text-xs font-mono">
          {eventTypes.map((et) => (
            <button
              key={et}
              onClick={() => setFilterType(et)}
              className={`px-3 py-1 rounded uppercase text-[10px] ${filterType === et ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" : "text-slate-400 hover:text-white"}`}
            >
              {et}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Strategy</th>
                <th className="py-3 px-4">Symbol</th>
                <th className="py-3 px-4 text-right">Timestamp</th>
                <th className="py-3 px-4 text-center">Payload</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((log) => (
                <tr key={log.id} className="hover:bg-slate-900/40 transition">
                  <td className="py-3 px-4">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                      {log.event_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-semibold text-white">{log.action}</td>
                  <td className="py-3 px-4 text-slate-300">{log.strategy_id || "SYSTEM"}</td>
                  <td className="py-3 px-4 text-white font-bold">{log.symbol || "—"}</td>
                  <td className="py-3 px-4 text-right text-slate-400 text-[11px]">
                    {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "Recent"}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => setSelectedEntry(log)}
                      className="text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-1 text-[11px] underline"
                    >
                      <Code2 className="w-3.5 h-3.5" /> View JSON
                    </button>
                  </td>
                </tr>
              ))}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No audit records matching filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* JSON Payload Inspection Modal */}
      {selectedEntry && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 max-w-xl w-full rounded-2xl p-6 shadow-2xl relative">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800">
              <h3 className="font-bold text-white text-sm">
                Audit Payload: {selectedEntry.event_type} ({selectedEntry.action})
              </h3>
              <button
                onClick={() => setSelectedEntry(null)}
                className="text-slate-400 hover:text-white text-xs bg-slate-800 px-2 py-1 rounded"
              >
                Close
              </button>
            </div>
            <pre className="text-xs text-cyan-300 font-mono bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-x-auto max-h-96">
              {JSON.stringify(selectedEntry.details || selectedEntry, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
