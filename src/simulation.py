from src.market_state_recorder import MarketStateRecorder
from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3
from src.synthetic_market import SyntheticMarket


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

    def run(self, num_events):
        for _ in range(num_events):
            # Coba membatalkan order yang sedang aktif.
            if (
                self.book.order_index
                and self.market.should_cancel_order()
            ):
                previous_book = self.book.snapshot()

                order_id = self.market.choose_order_to_cancel(
                    self.book.order_index.keys()
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

            # Jika tidak ada cancellation, proses order seperti biasa.
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