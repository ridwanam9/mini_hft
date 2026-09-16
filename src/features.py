def order_book_imbalance(book):

    bid_volume = sum(book.bids.values())
    ask_volume = sum(book.asks.values())

    total = bid_volume + ask_volume

    if total == 0:
        return 0

    return (bid_volume - ask_volume) / total