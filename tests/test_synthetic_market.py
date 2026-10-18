from src.synthetic_market import SyntheticMarket
from src.market_data import (
    OrderSide,
    OrderType,
)


def test_generator_creates_unique_order_ids():
    market = SyntheticMarket(seed=42)

    orders = [
        market.generate_order()
        for _ in range(100)
    ]

    order_ids = [
        order.order_id
        for order in orders
    ]

    assert len(order_ids) == len(set(order_ids))


def test_generator_produces_valid_orders():
    market = SyntheticMarket(seed=42)

    for _ in range(100):

        order = market.generate_order()

        assert order.quantity > 0
        assert order.order_id > 0

        if order.order_type == OrderType.LIMIT:
            assert order.price is not None
            assert order.price > 0

        if order.order_type == OrderType.MARKET:
            assert order.price is None


def test_generator_is_deterministic():
    market_a = SyntheticMarket(seed=42)
    market_b = SyntheticMarket(seed=42)

    orders_a = [
        market_a.generate_order()
        for _ in range(20)
    ]

    orders_b = [
        market_b.generate_order()
        for _ in range(20)
    ]

    assert orders_a == orders_b


def test_generator_contains_both_sides():
    market = SyntheticMarket(seed=42)

    orders = [
        market.generate_order()
        for _ in range(500)
    ]

    sides = {
        order.side
        for order in orders
    }

    assert OrderSide.BUY in sides
    assert OrderSide.SELL in sides

def test_generator_increments_timestamp():
    market = SyntheticMarket(
        time_step=0.001,
        seed=42,
    )

    order_1 = market.generate_order()
    order_2 = market.generate_order()
    order_3 = market.generate_order()

    assert order_1.timestamp == 0.001
    assert order_2.timestamp == 0.002
    assert order_3.timestamp == 0.003