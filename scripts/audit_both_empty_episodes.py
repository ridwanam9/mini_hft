from statistics import mean, median

from src.simulation import Simulation


NUM_EVENTS = 10_000
SEED = 42

simulation = Simulation(seed=SEED)
states = simulation.run(NUM_EVENTS)

episodes = []
current = None

for index, state in enumerate(states):
    both_empty = (
        state.best_bid is None
        and state.best_ask is None
    )

    if both_empty:
        if current is None:
            current = {
                "start": index,
                "timestamp": state.timestamp,
                "duration": 0,
            }
        current["duration"] += 1

    elif current is not None:
        current["end"] = index - 1
        current["recovered"] = True
        episodes.append(current)
        current = None

if current is not None:
    current["end"] = len(states) - 1
    current["recovered"] = False
    episodes.append(current)

print("=== BOTH-EMPTY EPISODE AUDIT ===")
print(f"Total events: {len(states)}")
print(f"BOTH_EMPTY episodes: {len(episodes)}")

recovered = [e for e in episodes if e["recovered"]]
unrecovered = [e for e in episodes if not e["recovered"]]

print(f"Recovered episodes: {len(recovered)}")
print(f"Unrecovered at end: {len(unrecovered)}")

if episodes:
    durations = [e["duration"] for e in episodes]
    print(f"Mean duration: {mean(durations):.2f} events")
    print(f"Median duration: {median(durations):.2f} events")
    print(f"Maximum duration: {max(durations)} events")

print("\n--- Longest episodes ---")
for episode in sorted(
    episodes,
    key=lambda e: e["duration"],
    reverse=True,
)[:10]:
    print(episode)

print("\n--- Final book ---")
print(f"Best bid: {simulation.book.best_bid}")
print(f"Best ask: {simulation.book.best_ask}")
print(f"Active orders: {len(simulation.book.order_index)}")
