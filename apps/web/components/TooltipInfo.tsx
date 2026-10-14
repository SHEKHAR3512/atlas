"use client";

import React, { useState } from "react";
import { HelpCircle } from "lucide-react";

export const GLOSSARY: Record<string, string> = {
  "Sharpe Ratio":
    "Measures excess return per unit of total risk (volatility). Benchmarked against risk-free rate (6.5%). Values > 1.0 indicate strong risk efficiency. Past performance does not guarantee future results.",
  "Sortino Ratio":
    "Measures excess return against harmful downside volatility only. Unlike Sharpe, it does not penalize upside volatility.",
  "Drawdown":
    "The peak-to-trough percentage decline in portfolio equity. ATLAS imposes hard circuit breakers at 8% maximum portfolio drawdown.",
  "Kelly Criterion":
    "A mathematical formula calculating optimal bet sizing to maximize expected logarithmic growth while minimizing probability of ruin. ATLAS uses a conservative Quarter-Kelly (0.25x) capped at 3% per position.",
  "Expectancy":
    "The average amount of money earned or lost per rupee risked over a large sequence of trades. Must remain strictly positive for strategy survival.",
  "Profit Factor":
    "Gross profits divided by gross losses. A profit factor above 1.25 indicates robust gross profitability net of spread.",
  "Volatility":
    "Annualized standard deviation of returns. Higher volatility indicates wider price dispersion and calls for smaller position sizes.",
  "Exposure":
    "The percentage of total portfolio equity currently invested in active equity positions vs retained in risk-free cash.",
  "Market Regime":
    "Classification of prevailing macroeconomic and market state (Bull Trend, Bear Trend, Sideways, High Volatility, Crisis). Strategies only trade in their compatible regimes.",
};

interface TooltipProps {
  term: keyof typeof GLOSSARY | string;
}

export const TooltipInfo: React.FC<TooltipProps> = ({ term }) => {
  const [isOpen, setIsOpen] = useState(false);
  const text = GLOSSARY[term] || "Quantitative risk parameter.";

  return (
    <div className="relative inline-flex items-center ml-1">
      <button
        type="button"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        onClick={() => setIsOpen(!isOpen)}
        className="text-slate-400 hover:text-cyan-400 transition-colors p-0.5"
        aria-label={`Info about ${term}`}
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </button>

      {isOpen && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-2.5 bg-slate-900/95 border border-slate-700 rounded-lg shadow-xl text-xs text-slate-300 z-50 backdrop-blur pointer-events-none">
          <div className="font-semibold text-cyan-400 mb-1">{term}</div>
          <p className="leading-relaxed">{text}</p>
        </div>
      )}
    </div>
  );
};
