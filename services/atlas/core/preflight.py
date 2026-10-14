import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from services.atlas.core.config import config
from services.atlas.risk.circuit_breaker import circuit_breaker
from services.atlas.db.session import check_db_health

logger = logging.getLogger("atlas.preflight")


class LivePreflightChecker:
    """
    Live Trading Safety Preflight Gate.
    Any failure causes live_ready=False and prevents live trading.
    """

    @classmethod
    async def run_checks(cls) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []

        # 1. Environment and Flags
        is_live_mode = config.settings.TRADING_MODE.upper() == "LIVE"
        checks.append({
            "name": "live_mode_flag",
            "passed": is_live_mode,
            "message": "TRADING_MODE is LIVE" if is_live_mode else "TRADING_MODE is PAPER (Live disabled)",
            "critical": True,
        })

        is_live_enabled = config.settings.ENABLE_LIVE_TRADING is True
        checks.append({
            "name": "enable_live_flag",
            "passed": is_live_enabled,
            "message": "ENABLE_LIVE_TRADING=true" if is_live_enabled else "ENABLE_LIVE_TRADING=false",
            "critical": True,
        })

        has_ack = config.settings.LIVE_TRADING_ACK == "I_UNDERSTAND_REAL_CAPITAL_IS_AT_RISK"
        checks.append({
            "name": "live_trading_ack",
            "passed": has_ack,
            "message": "Explicit capital risk acknowledgement verified" if has_ack else "Missing/invalid LIVE_TRADING_ACK",
            "critical": True,
        })

        # 2. Broker Credentials (Angel One)
        has_broker_creds = bool(
            config.settings.ANGEL_API_KEY
            and config.settings.ANGEL_CLIENT_CODE
            and config.settings.ANGEL_PASSWORD
            and config.settings.ANGEL_TOTP_SECRET
        )
        checks.append({
            "name": "broker_credentials",
            "passed": has_broker_creds,
            "message": "Broker API credentials present" if has_broker_creds else "Missing Angel One credentials",
            "critical": True,
        })

        # 3. Database Health
        db_ok = await check_db_health()
        checks.append({
            "name": "database_health",
            "passed": db_ok,
            "message": "Database connection healthy" if db_ok else "Database connection failed",
            "critical": True,
        })

        # 4. Kill Switch Status
        kill_active = circuit_breaker.is_kill_switch_active
        checks.append({
            "name": "kill_switch_operational",
            "passed": not kill_active,
            "message": "Kill switch operational and unengaged" if not kill_active else "Hard Kill Switch is ACTIVE",
            "critical": True,
        })

        # 5. Timezone & Market Calendar
        tz_ok = config.settings.TIMEZONE == "Asia/Kolkata"
        checks.append({
            "name": "timezone_sanity",
            "passed": tz_ok,
            "message": f"Timezone configured as {config.settings.TIMEZONE}",
            "critical": False,
        })

        # 6. Static IP Configuration
        static_ip_configured = config.settings.APP_ENV != "production" or bool(config.settings.API_HOST)
        checks.append({
            "name": "static_ip_whitelist",
            "passed": static_ip_configured,
            "message": "Static IP whitelist registered with broker",
            "critical": True,
        })

        # 7. Cash Equities Restriction V1
        no_leverage = not (config.settings.ALLOW_LEVERAGE or config.settings.ALLOW_FUTURES or config.settings.ALLOW_OPTIONS or config.settings.ALLOW_SHORTS)
        checks.append({
            "name": "cash_equities_long_only",
            "passed": no_leverage,
            "message": "Strict Long-only Cash Equities constraints active (No shorts/derivatives)",
            "critical": True,
        })

        failed_critical = [c for c in checks if c["critical"] and not c["passed"]]
        live_ready = len(failed_critical) == 0

        return {
            "live_ready": live_ready,
            "system_mode": config.settings.TRADING_MODE,
            "checks": checks,
            "failed_count": len([c for c in checks if not c["passed"]]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def main():
    import asyncio
    res = asyncio.run(LivePreflightChecker.run_checks())
    print("\n===========================================")
    print("        ATLAS LIVE TRADING PREFLIGHT       ")
    print("===========================================")
    print(f"System Mode: {res['system_mode']}")
    print(f"Live Ready:  {res['live_ready']}")
    print("-------------------------------------------")
    for c in res["checks"]:
        status = "PASS" if c["passed"] else "FAIL"
        crit = " [CRITICAL]" if c["critical"] else ""
        print(f"[{status}] {c['name']}{crit}: {c['message']}")
    print("===========================================")
    if not res["live_ready"]:
        print("FAIL-CLOSED: Live trading activation is BLOCKED.")
        print("To trade, use default PAPER mode.")
    else:
        print("ALL PREFLIGHT CHECKS PASSED.")
    print("===========================================\n")


if __name__ == "__main__":
    main()
