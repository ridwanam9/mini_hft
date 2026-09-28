def best_bid(book):
    return book.best_bid


def best_ask(book):
    return book.best_ask


def spread(book):
    if book.best_bid is None or book.best_ask is None:
        return None

    return book.best_ask - book.best_bid


def mid_price(book):
    if book.best_bid is None or book.best_ask is None:
        return None

    return (book.best_bid + book.best_ask) / 2


def bid_volume(book, levels=None):
    bids = sorted(
        book.bids.items(),
        reverse=True
    )

    if levels is not None:
        bids = bids[:levels]

    return sum(quantity for _, quantity in bids)


def ask_volume(book, levels=None):
    asks = sorted(
        book.asks.items()
    )

    if levels is not None:
        asks = asks[:levels]

    return sum(quantity for _, quantity in asks)


def order_book_imbalance(book, levels=None):

    bid_vol = bid_volume(book, levels)
    ask_vol = ask_volume(book, levels)

    total = bid_vol + ask_vol

    if total == 0:
        return 0.0

    return (bid_vol - ask_vol) / total