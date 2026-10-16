from dataclasses import dataclass

@dataclass
class TradeRecord:
    timestamp : float
    price : float
    quantity : int
    aggressor : str
    buy_order_id : int
    sell_order_id : int

