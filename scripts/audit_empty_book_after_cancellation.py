
from collections import Counter

from src.simulation import Simulation


NUM_EVENTS = 10_000
SEED = 42

simulation = Simulation(seed=SEED)
states = simulation.run(NUM_EVENTS)

# Hitung kondisi order book dari setiap market state.
conditions = Counter()
first_empty = None
last_nonempty = None
longest_empty_run = 0
current_empty_run = 0

for index, state in enumerate(states):
    bid = state.best_bid
    ask = state.best_ask

    if bid is not None and ask is not None:
        condition = "BOTH_PRESENT"
        last_nonempty = index
        current_empty_run = 0
    elif bid is not None:
        condition = "ASK_EMPTY"
        current_empty_run += 1
    elif ask is not None:
        condition = "BID_EMPTY"
        current_empty_run += 1
    else:
        condition = "BOTH_EMPTY"
        current_empty_run += 1

    conditions[condition] += 1
    longest_empty_run = max(longest_empty_run, current_empty_run)

    if condition != "BOTH_PRESENT" and first_empty is None:
        first_empty = (index, condition, state.timestamp)

print("=== EMPTY BOOK AUDIT ===")
print(f"Events: {len(states)}")

for condition in (
    "BOTH_PRESENT",
    "BID_EMPTY",
    "ASK_EMPTY",
    "BOTH_EMPTY",
):
    count = conditions[condition]
    print(f"{condition:15s}: {count:5d} ({count / len(states):.2%})")

print("\n--- Timeline ---")
print(f"First non-two-sided state: {first_empty}")
print(f"Last two-sided state index: {last_nonempty}")
print(f"Longest consecutive non-two-sided run: {longest_empty_run}")

print("\n--- Lifecycle ---")
status_counts = Counter(
    record["status"]
    for record in simulation.book.order_history.values()
)
for status, count in sorted(status_counts.items()):
    print(f"{status:10s}: {count}")

print("\n--- Final book ---")
print(f"Best bid: {simulation.book.best_bid}")
print(f"Best ask: {simulation.book.best_ask}")
print(f"Active orders: {len(simulation.book.order_index)}")
print(f"Trade records: {len(simulation.engine.trade_tape)}")


