from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "ATLAS"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    WEB_PORT: int = 3000

    POSTGRES_DB: str = "atlas"
    POSTGRES_USER: str = "atlas"
    POSTGRES_PASSWORD: str = "atlas_local"
    DATABASE_URL: str = "postgresql+psycopg://atlas:atlas_local@postgres:5432/atlas"
    SQLITE_FALLBACK: bool = True
    REDIS_URL: str = "redis://redis:6379/0"

    TRADING_MODE: str = "PAPER"
    ENABLE_LIVE_TRADING: bool = False
    LIVE_TRADING_ACK: Optional[str] = None

    BASE_CURRENCY: str = "INR"
    INITIAL_PAPER_CAPITAL: float = 100000.0

    MARKET: str = "NSE"
    TIMEZONE: str = "Asia/Kolkata"

    KELLY_FRACTION: float = 0.25
    MAX_POSITION_PCT: float = 0.03
    MAX_SECTOR_EXPOSURE_PCT: float = 0.15
    MAX_GROSS_EXPOSURE_PCT: float = 0.60
    MAX_DAILY_LOSS_PCT: float = 0.015
    MAX_WEEKLY_LOSS_PCT: float = 0.04
    MAX_PORTFOLIO_DRAWDOWN_PCT: float = 0.08
    MAX_CORRELATED_POSITIONS: int = 3
    MIN_BACKTEST_TRADES: int = 100
    MAX_ORDER_NOTIONAL_PCT: float = 0.03
    MAX_SLIPPAGE_BPS: float = 20.0

    ALLOW_SHORTS: bool = False
    ALLOW_MARGIN: bool = False
    ALLOW_FUTURES: bool = False
    ALLOW_OPTIONS: bool = False
    ALLOW_LEVERAGE: bool = False
    HARD_KILL_SWITCH: bool = True

    BROKER: str = "paper"
    ANGEL_API_KEY: Optional[str] = None
    ANGEL_CLIENT_CODE: Optional[str] = None
    ANGEL_PASSWORD: Optional[str] = None
    ANGEL_TOTP_SECRET: Optional[str] = None

    AI_PROVIDER: str = "disabled"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: Optional[str] = None

    PROMETHEUS_ENABLED: bool = True


def get_project_root() -> Path:
    # Anchor to scratch/atlas directory
    return Path(__file__).resolve().parent.parent.parent.parent


def load_yaml_config(relative_path: str) -> Dict[str, Any]:
    root = get_project_root()
    filepath = root / relative_path
    if not filepath.exists():
        # Fallback check
        alt_path = Path(relative_path)
        if alt_path.exists():
            filepath = alt_path
        else:
            return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class RuntimeConfig:
    """
    Immutable Runtime Configuration container.
    Guarantees deterministic risk limits and fail-closed safety.
    """
    def __init__(self):
        self.settings = AppSettings()
        self.risk_yaml = load_yaml_config("config/risk.yaml")
        self.markets_yaml = load_yaml_config("config/markets.yaml")
        self.cost_model_yaml = load_yaml_config("config/costs/nse_equity_v1.yaml")
        self.strategies_yaml = load_yaml_config("config/strategies.yaml")
        self.research_yaml = load_yaml_config("config/research.yaml")

        self._validate_fail_closed()

    def _validate_fail_closed(self):
        # Strict rule: LIVE trading requires explicit ACK and ENABLE_LIVE_TRADING=true
        if self.settings.TRADING_MODE.upper() == "LIVE":
            if not self.settings.ENABLE_LIVE_TRADING:
                raise RuntimeError(
                    "FAIL CLOSED: TRADING_MODE is LIVE but ENABLE_LIVE_TRADING is false."
                )
            if self.settings.LIVE_TRADING_ACK != "I_UNDERSTAND_REAL_CAPITAL_IS_AT_RISK":
                raise RuntimeError(
                    "FAIL CLOSED: Live trading requires LIVE_TRADING_ACK=I_UNDERSTAND_REAL_CAPITAL_IS_AT_RISK"
                )

        # Enforce no leverage/derivatives for cash equities V1
        if self.settings.ALLOW_LEVERAGE or self.settings.ALLOW_FUTURES or self.settings.ALLOW_OPTIONS or self.settings.ALLOW_SHORTS:
            raise RuntimeError(
                "FAIL CLOSED: V1 allows long-only cash equities without leverage or derivatives."
            )

    @property
    def is_live(self) -> bool:
        return (
            self.settings.TRADING_MODE.upper() == "LIVE"
            and self.settings.ENABLE_LIVE_TRADING is True
            and self.settings.LIVE_TRADING_ACK == "I_UNDERSTAND_REAL_CAPITAL_IS_AT_RISK"
        )

    @property
    def symbols(self) -> List[Dict[str, Any]]:
        return self.markets_yaml.get("universe", {}).get("symbols", [])


# Global singleton instance
config = RuntimeConfig()
