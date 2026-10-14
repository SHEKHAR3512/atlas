import math
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


class BacktestMetricsCalculator:
    """
    Comprehensive quantitative performance and risk metrics engine.
    Calculates net of transaction costs and slippage.
    """

    @staticmethod
    def calculate_metrics(
        equity_series: pd.Series,
        trades: List[Dict[str, any]],
        initial_capital: float = 100000.0,
        risk_free_rate: float = 0.065 # 6.5% typical RBI repo rate benchmark
    ) -> Dict[str, float]:
        if equity_series.empty or len(equity_series) < 2:
            return {
                "total_return_pct": 0.0,
                "cagr_pct": 0.0,
                "annualized_volatility": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "drawdown_duration_bars": 0,
                "trades_count": len(trades),
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "payoff_ratio": 0.0,
                "var_95": 0.0,
                "cvar_95": 0.0,
            }

        # Daily returns
        daily_returns = equity_series.pct_change().dropna()
        final_equity = float(equity_series.iloc[-1])
        total_return = (final_equity - initial_capital) / initial_capital

        # CAGR
        days = max(1, len(equity_series))
        years = days / 252.0
        cagr = ((final_equity / initial_capital) ** (1.0 / max(years, 0.01))) - 1.0 if final_equity > 0 else -1.0

        # Volatility
        ann_vol = float(daily_returns.std() * np.sqrt(252)) if len(daily_returns) > 1 else 0.0

        # Sharpe Ratio
        excess_returns = daily_returns - (risk_free_rate / 252.0)
        mean_excess = float(excess_returns.mean() * 252)
        sharpe = (mean_excess / ann_vol) if ann_vol > 1e-6 else 0.0

        # Downside Volatility / Sortino
        negative_returns = daily_returns[daily_returns < 0]
        downside_std = float(negative_returns.std() * np.sqrt(252)) if len(negative_returns) > 1 else 1e-4
        sortino = (mean_excess / downside_std) if downside_std > 1e-6 else 0.0

        # Drawdown analysis
        cum_max = equity_series.cummax()
        drawdowns = (equity_series - cum_max) / cum_max
        max_dd = float(drawdowns.min()) # negative number, e.g. -0.08
        abs_max_dd = abs(max_dd)

        # Max drawdown duration
        in_drawdown = drawdowns < 0
        dd_lengths = []
        curr_len = 0
        for val in in_drawdown:
            if val:
                curr_len += 1
            else:
                if curr_len > 0:
                    dd_lengths.append(curr_len)
                curr_len = 0
        if curr_len > 0:
            dd_lengths.append(curr_len)
        max_dd_duration = max(dd_lengths) if dd_lengths else 0

        # Calmar Ratio
        calmar = (cagr / abs_max_dd) if abs_max_dd > 1e-6 else 0.0

        # Value at Risk (VaR 95%) & CVaR (Expected Shortfall)
        if len(daily_returns) > 10:
            var_95 = float(np.percentile(daily_returns, 5))
            cvar_95 = float(daily_returns[daily_returns <= var_95].mean())
        else:
            var_95 = 0.0
            cvar_95 = 0.0

        # Trade Statistics
        trade_count = len(trades)
        if trade_count > 0:
            pnl_list = [float(t.get("net_pnl", 0.0)) for t in trades]
            ret_list = [float(t.get("return_pct", 0.0)) for t in trades]
            winning_trades = [p for p in pnl_list if p > 0]
            losing_trades = [p for p in pnl_list if p <= 0]

            win_count = len(winning_trades)
            win_rate = win_count / trade_count

            gross_profits = sum(winning_trades)
            gross_losses = abs(sum(losing_trades))

            profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else (99.0 if gross_profits > 0 else 0.0)

            avg_win = float(np.mean([r for r in ret_list if r > 0])) if winning_trades else 0.0
            avg_loss = float(np.mean([r for r in ret_list if r <= 0])) if losing_trades else 0.0
            abs_avg_loss = abs(avg_loss)

            payoff_ratio = (avg_win / abs_avg_loss) if abs_avg_loss > 0 else (99.0 if avg_win > 0 else 0.0)

            # Mathematical Expectancy = (p * avg_win) - (q * abs_avg_loss)
            q = 1.0 - win_rate
            expectancy = (win_rate * avg_win) - (q * abs_avg_loss)
        else:
            win_rate = 0.0
            profit_factor = 0.0
            expectancy = 0.0
            avg_win = 0.0
            avg_loss = 0.0
            payoff_ratio = 0.0

        return {
            "total_return_pct": round(total_return, 4),
            "cagr_pct": round(cagr, 4),
            "annualized_volatility": round(ann_vol, 4),
            "sharpe_ratio": round(sharpe, 3),
            "sortino_ratio": round(sortino, 3),
            "calmar_ratio": round(calmar, 3),
            "max_drawdown_pct": round(abs_max_dd, 4),
            "drawdown_duration_bars": max_dd_duration,
            "trades_count": trade_count,
            "win_rate": round(win_rate, 4),
            "profit_factor": round(profit_factor, 3),
            "expectancy": round(expectancy, 4),
            "average_win": round(avg_win, 4),
            "average_loss": round(avg_loss, 4),
            "payoff_ratio": round(payoff_ratio, 3),
            "var_95": round(var_95, 4),
            "cvar_95": round(cvar_95, 4),
        }
