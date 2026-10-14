"use client";

import React from "react";
import { AlertOctagon, ShieldAlert, CheckCircle } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  isKillActive: boolean;
  onConfirmKill: () => void;
  onResetKill: () => void;
}

export const KillSwitchModal: React.FC<Props> = ({
  isOpen,
  onClose,
  isKillActive,
  onConfirmKill,
  onResetKill,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 max-w-md w-full rounded-2xl p-6 shadow-2xl relative">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center border border-rose-500/30">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Emergency Hard Kill Switch</h3>
            <p className="text-xs text-slate-400 font-mono">FAIL-CLOSED PROTOCOL</p>
          </div>
        </div>

        <div className="text-xs text-slate-300 space-y-2 mb-6 bg-slate-950/60 p-3.5 rounded-lg border border-slate-800">
          <p className="font-semibold text-rose-300">
            {isKillActive
              ? "The Kill Switch is currently ENGAGED. All strategy signals and new order entries are strictly blocked."
              : "Engaging the kill switch will immediately:"}
          </p>
          <ul className="list-disc pl-4 space-y-1 text-slate-400">
            <li>Halt all strategy execution engines immediately</li>
            <li>Block all pending and proposed order entries</li>
            <li>Cancel outstanding unfilled entry orders</li>
            <li>Preserve position books, monitoring, and audit trails</li>
          </ul>
        </div>

        <div className="flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
          >
            Close
          </button>

          {isKillActive ? (
            <button
              onClick={() => {
                onResetKill();
                onClose();
              }}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-emerald-300 bg-emerald-950/80 border border-emerald-500/50 hover:bg-emerald-900 transition flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Reset & Arm Kill Switch
            </button>
          ) : (
            <button
              onClick={() => {
                onConfirmKill();
                onClose();
              }}
              className="px-4 py-2 rounded-lg text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 transition flex items-center gap-2 shadow-lg shadow-rose-600/30"
            >
              <ShieldAlert className="w-4 h-4" />
              TRIGGER KILL SWITCH NOW
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
