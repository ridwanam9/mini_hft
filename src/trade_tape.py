from dataclasses import dataclass


@dataclass
class TradeRecord:
    timestamp: float
    price: float
    quantity: int
    aggressor: str
    buy_order_id: int
    sell_order_id: int
    arrival_mid_price: float | None = None
    arrival_best_bid: float | None = None
    arrival_best_ask: float | None = None
    arrival_spread: float | None = None
