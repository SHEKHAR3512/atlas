from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Broker(ABC):

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection or session with the broker."""
        pass

    @abstractmethod
    async def account(self) -> Dict[str, Any]:
        """Fetch account balances, cash, margin, and collateral."""
        pass

    @abstractmethod
    async def positions(self) -> List[Dict[str, Any]]:
        """Fetch current open and closed positions from broker."""
        pass

    @abstractmethod
    async def orders(self) -> List[Dict[str, Any]]:
        """Fetch active and historic orders."""
        pass

    @abstractmethod
    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place limit or market order.
        Must enforce idempotency with client_order_id.
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        pass

    @abstractmethod
    async def market_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch current quote / tick for symbol."""
        pass
