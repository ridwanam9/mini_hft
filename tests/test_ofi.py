from src.ofi import calculate_ofi
from src.order_book_l3 import OrderBookL3
from src.market_data import Order, OrderSide, OrderType


def make_order(order_id, side, quantity, price):
    return Order(
        order_id=order_id,
        side=side,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
    )


def test_bid_size_increase_produces_positive_ofi():
    previous = OrderBookL3()
    current = OrderBookL3()

    previous.add_resting_order(
        make_order(1, OrderSide.BUY, 100, 101.00)
    )

    current.add_resting_order(
        make_order(2, OrderSide.BUY, 150, 101.00)
    )

    assert calculate_ofi(previous, current) == 50


def test_bid_size_decrease_produces_negative_ofi():
    previous = OrderBookL3()
    current = OrderBookL3()

    previous.add_resting_order(
        make_order(1, OrderSide.BUY, 100, 101.00)
    )

    current.add_resting_order(
        make_order(2, OrderSide.BUY, 60, 101.00)
    )

    assert calculate_ofi(previous, current) == -40


def test_ask_size_increase_produces_negative_ofi():
    previous = OrderBookL3()
    current = OrderBookL3()

    previous.add_resting_order(
        make_order(1, OrderSide.SELL, 100, 101.02)
    )

    current.add_resting_order(
        make_order(2, OrderSide.SELL, 150, 101.02)
    )

    assert calculate_ofi(previous, current) == -50


def test_ask_size_decrease_produces_positive_ofi():
    previous = OrderBookL3()
    current = OrderBookL3()

    previous.add_resting_order(
        make_order(1, OrderSide.SELL, 100, 101.02)
    )

    current.add_resting_order(
        make_order(2, OrderSide.SELL, 60, 101.02)
    )

    assert calculate_ofi(previous, current) == 40