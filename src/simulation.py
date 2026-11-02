from src.market_state_recorder import MarketStateRecorder
from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3
from src.synthetic_market import SyntheticMarket
from src.market_data import OrderSide
import random


class Simulation:
    def __init__(
        self,
        seed=None,
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
        cancellation_probability=0.10,
        cancellation_policy="distance",
    ):
        if cancellation_policy not in {"none", "random", "distance"}:
            raise ValueError(
                "cancellation_policy must be "
                "'none', 'random', or 'distance'"
            )

        self.cancellation_random = random.Random(
            None if seed is None else seed + 1_000_003
        )

        self.cancellation_policy = cancellation_policy

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
        """Return active orders whose cancellation won't remove
        the last resting order from their side.
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

    def should_cancel_order(self):
        return (
            self.cancellation_random.random()
            < self.market.cancellation_probability
        )


    def choose_order_to_cancel_random(self, eligible_ids):
        if not eligible_ids:
            return None

        return self.cancellation_random.choice(eligible_ids)

    def run(self, num_events):
        for _ in range(num_events):
            cancellable_ids = self.get_cancellable_order_ids()

            should_cancel = (
                self.cancellation_policy != "none"
                and bool(cancellable_ids)
                and self.should_cancel_order()
            )

            if should_cancel:
                previous_book = self.book.snapshot()

                if self.cancellation_policy == "random":
                    order_id = self.choose_order_to_cancel_random(cancellable_ids)
                else:
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

            # If cancellation does not occur, generate and process a new order.
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

    def run_until_submissions(self, target_submissions, max_events=None):
        """Run until the target number of orders has been submitted."""
        if target_submissions < 0:
            raise ValueError("target_submissions must be non-negative")

        if max_events is None:
            max_events = target_submissions * 3 + 100

        events_processed = 0

        while len(self.book.order_history) < target_submissions:
            if events_processed >= max_events:
                raise RuntimeError(
                    "Maximum events reached before target submissions"
                )

            self.run(1)
            events_processed += 1

        return self.state_recorder.states
