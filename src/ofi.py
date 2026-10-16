def calculate_ofi(previous_book, current_book):
    previous_bid = previous_book.best_bid
    current_bid = current_book.best_bid

    previous_ask = previous_book.best_ask
    current_ask = current_book.best_ask

    previous_bid_size = (
        previous_book.bids.get(previous_bid, 0)
        if previous_bid is not None
        else 0
    )

    current_bid_size = (
        current_book.bids.get(current_bid, 0)
        if current_bid is not None
        else 0
    )

    previous_ask_size = (
        previous_book.asks.get(previous_ask, 0)
        if previous_ask is not None
        else 0
    )

    current_ask_size = (
        current_book.asks.get(current_ask, 0)
        if current_ask is not None
        else 0
    )

    # Bid contribution
    if previous_bid is None and current_bid is None:
        bid_event = 0

    elif previous_bid is None:
        bid_event = current_bid_size

    elif current_bid is None:
        bid_event = -previous_bid_size

    elif current_bid > previous_bid:
        bid_event = current_bid_size

    elif current_bid == previous_bid:
        bid_event = current_bid_size - previous_bid_size

    else:
        bid_event = -previous_bid_size

    # Ask contribution
    if previous_ask is None and current_ask is None:
        ask_event = 0

    elif previous_ask is None:
        ask_event = -current_ask_size

    elif current_ask is None:
        ask_event = previous_ask_size

    elif current_ask < previous_ask:
        ask_event = -current_ask_size

    elif current_ask == previous_ask:
        ask_event = -(current_ask_size - previous_ask_size)

    else:
        ask_event = previous_ask_size

    return bid_event + ask_event

