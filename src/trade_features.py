def trade_imbalance(trades):
    buy_volume = sum(
        trade.quantity
        for trade in trades
        if trade.aggressor == "BUY"
    )

    sell_volume = sum(
        trade.quantity
        for trade in trades
        if trade.aggressor == "SELL"
    )

    total = buy_volume + sell_volume
    if total == 0:
        return 0.0

    return (buy_volume - sell_volume) / total

