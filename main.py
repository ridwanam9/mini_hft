from src.order_book import OrderBook
from src.simulator import MarketSimulator
from src.features import get_features


book = OrderBook()

simulator = MarketSimulator(
    start_price=100.00
)


for i in range(100):

    timestamp = i * 0.001

    event = simulator.generate_event(
        timestamp
    )

    book.process_event(event)

    features = get_features(book)

    print(
        timestamp,
        features
    )