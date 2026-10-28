
from collections import Counter

from src.simulation import Simulation


NUM_EVENTS = 10_000
SEED = 42

simulation = Simulation(seed=SEED)
states = simulation.run(NUM_EVENTS)

history = simulation.book.order_history
status_counts = Counter(
    record["status"] for record in history.values()
)

active_orders = list(simulation.book.order_index.values())
active_order_objects = [
    entry[2] for entry in active_orders
]

current_time = simulation.market.timestamp

cancelled = [
    record
    for record in history.values()
    if record["status"] == "cancelled"
]

filled = [
    record
    for record in history.values()
    if record["status"] == "filled"
]

expired = [
    record
    for record in history.values()
    if record["status"] == "expired"
]

active = [
    record
    for record in history.values()
    if record["status"] == "active"
]

print("=== PHASE 20.5.1: CANCELLATION AUDIT ===")
print(f"Requested events: {NUM_EVENTS}")
print(f"Recorded market states: {len(states)}")
print(f"Final simulation time: {current_time:.6f}")
print(f"Total submitted orders: {len(history)}")
print(f"Trade records: {len(simulation.engine.trade_tape)}")

print("\n--- Order lifecycle ---")
for status in ("filled", "active", "cancelled", "expired"):
    print(f"{status:10s}: {status_counts[status]}")

print("\n--- Cancellation details ---")
print(f"Cancelled orders: {len(cancelled)}")

if cancelled:
    print(
        "Cancellation rate among submitted orders: "
        f"{len(cancelled) / len(history):.2%}"
    )

print("\n--- Remaining active orders ---")
print(f"Active orders: {len(active_order_objects)}")

if active_order_objects:
    ages = [
        current_time - order.timestamp
        for order in active_order_objects
    ]

    print(f"Average age: {sum(ages) / len(ages):.6f} seconds")
    print(f"Maximum age: {max(ages):.6f} seconds")

print("\n--- Final order book ---")
print(f"Best bid: {simulation.book.best_bid}")
print(f"Best ask: {simulation.book.best_ask}")
print(f"Spread: {simulation.book.spread}")
print(f"Bid levels: {len(simulation.book.bid_orders)}")
print(f"Ask levels: {len(simulation.book.ask_orders)}")

print("\n--- Validation ---")
print(f"Lifecycle accounted for: {sum(status_counts.values()) == len(history)}")
print(f"All events recorded: {len(states) == NUM_EVENTS}")
print(
    "Order IDs unique: "
    f"{len(simulation.book.seen_order_ids) == len(history)}"
)
