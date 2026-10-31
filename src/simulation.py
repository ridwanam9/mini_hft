from src.market_state_recorder import MarketStateRecorder
from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3
from src.synthetic_market import SyntheticMarket
from src.market_data import OrderSide


class Simulation:
    def __init__(
        self,
        seed=None,
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
        cancellation_probability=0.10,
    ):
        self.market = SyntheticMarket(
            start_price=start_price,
            tick_size=tick_size,
            time_step=time_step,
            seed=seed,
            cancellation_probability=cancellation_probability,
        )

        self.book = OrderBookL3()
        self.engine = MatchingEngineL3(self.book)
        self.state_recorder = MarketStateRecorder()

    
    def get_cancellable_order_ids(self):
        """Return active orders whose cancellation won't
        remove the last resting order from their side.
        """
        bid_order_ids = []
        ask_order_ids = []

        for order_id, (side, price, order) in self.book.order_index.items():
            if side == OrderSide.BUY:
                bid_order_ids.append(order_id)
            elif side == OrderSide.SELL:
                ask_order_ids.append(order_id)

        eligible_ids = []

        if len(bid_order_ids) > 1:
            eligible_ids.extend(bid_order_ids)

        if len(ask_order_ids) > 1:
            eligible_ids.extend(ask_order_ids)

        return eligible_ids


    def run(self, num_events):
        for _ in range(num_events):
            # Phase 20.5.5.1: Protect the last resting order.
            cancellable_ids = self.get_cancellable_order_ids()

            if (
                cancellable_ids
                and self.market.should_cancel_order()
            ):
                previous_book = self.book.snapshot()

                order_id = self.choose_order_to_cancel_by_distance(
                    cancellable_ids
                )

                timestamp = self.market.next_timestamp()

                self.book.cancel_order(
                    order_id,
                    timestamp=timestamp,
                )

                current_book = self.book.snapshot()

                self.state_recorder.record(
                    previous_book=previous_book,
                    current_book=current_book,
                    timestamp=timestamp,
                    trade=None,
                )

                continue

            # Jika tidak melakukan cancellation,
            # lanjutkan dengan pembuatan dan pemrosesan order baru.
            order = self.market.generate_order()

            previous_book = self.book.snapshot()
            tape_length_before = len(self.engine.trade_tape)

            self.engine.submit_order(order)

            current_book = self.book.snapshot()
            new_trades = self.engine.trade_tape[tape_length_before:]
            last_trade = new_trades[-1] if new_trades else None

            self.state_recorder.record(
                previous_book=previous_book,
                current_book=current_book,
                timestamp=order.timestamp,
                trade=last_trade,
            )


        return self.state_recorder.states

    
    def choose_order_to_cancel_by_distance(self, eligible_ids):
        """Choose the eligible order farthest from fair value."""
        if not eligible_ids:
            return None

        fair_value = self.market.fair_value

        return max(
            eligible_ids,
            key=lambda order_id: abs(
                self.book.order_index[order_id][1] - fair_value
            ),
        )
