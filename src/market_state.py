from dataclasses import dataclass

@dataclass
class MarketState:
    timestamp: float

    best_bid: float | None
    best_ask: float | None

    spread: float | None
    mid_price: float | None

    bid_volume: int
    ask_volume: int

    obi: float
    microprice: float | None

    ofi: float

    last_trade_price: float | None
    last_trade_quantity: int
    last_trade_aggressor: str | None

    