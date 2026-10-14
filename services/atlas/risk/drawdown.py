import logging
from typing import Tuple
from services.atlas.core.config import config

logger = logging.getLogger("atlas.risk.drawdown")


class DrawdownMonitor:
    """
    Monitors daily loss, weekly loss, and peak-to-trough portfolio drawdown.
    Fails closed if loss limits are breached.
    """

    def __init__(self):
        self.max_daily_loss_pct = config.settings.MAX_DAILY_LOSS_PCT       # 1.5%
        self.max_weekly_loss_pct = config.settings.MAX_WEEKLY_LOSS_PCT     # 4.0%
        self.max_drawdown_pct = config.settings.MAX_PORTFOLIO_DRAWDOWN_PCT # 8.0%

    def check_drawdown_limits(
        self,
        current_equity: float,
        start_of_day_equity: float,
        start_of_week_equity: float,
        high_water_mark: float,
    ) -> Tuple[bool, str]:
        if high_water_mark <= 0 or current_equity <= 0:
            return True, "Baseline equity not set"

        # 1. Peak-to-Trough Drawdown
        current_dd = (high_water_mark - current_equity) / high_water_mark
        if current_dd >= self.max_drawdown_pct:
            return False, f"Portfolio drawdown breach: {round(current_dd*100, 2)}% exceeds max {self.max_drawdown_pct*100}%"

        # 2. Daily Loss
        if start_of_day_equity > 0:
            daily_loss = (start_of_day_equity - current_equity) / start_of_day_equity
            if daily_loss >= self.max_daily_loss_pct:
                return False, f"Daily loss breach: {round(daily_loss*100, 2)}% exceeds limit {self.max_daily_loss_pct*100}%"

        # 3. Weekly Loss
        if start_of_week_equity > 0:
            weekly_loss = (start_of_week_equity - current_equity) / start_of_week_equity
            if weekly_loss >= self.max_weekly_loss_pct:
                return False, f"Weekly loss breach: {round(weekly_loss*100, 2)}% exceeds limit {self.max_weekly_loss_pct*100}%"

        return True, "Drawdown within limits"
