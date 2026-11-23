
from dataclasses import dataclass


@dataclass
class TradeRecord:
    timestamp: float
    price: float
    quantity: int
    aggressor: str
    buy_order_id: int
    sell_order_id: int

    # Arrival price information
    arrival_mid_price: float | None = None
    arrival_best_bid: float | None = None
    arrival_best_ask: float | None = None
    arrival_spread: float | None = None

    # Arrival liquidity information
    arrival_bid_depth: int | None = None
    arrival_ask_depth: int | None = None
    arrival_obi: float | None = None
