
from collections import Counter, defaultdict
from statistics import mean, median

from src.simulation import Simulation


NUM_EVENTS = 10_000
SEED = 42


def classify_book(state):
    if state.best_bid is not None and state.best_ask is not None:
        return "BOTH_PRESENT"
    if state.best_bid is not None:
        return "ASK_EMPTY"
    if state.best_ask is not None:
        return "BID_EMPTY"
    return "BOTH_EMPTY"


simulation = Simulation(seed=SEED)
states = simulation.run(NUM_EVENTS)

# Episode dimulai ketika book kehilangan setidaknya satu sisi.
# Episode berakhir ketika kedua sisi tersedia kembali.
episodes = []
current_episode = None

for index, state in enumerate(states):
    condition = classify_book(state)

    if condition != "BOTH_PRESENT":
        if current_episode is None:
            current_episode = {
                "start_index": index,
                "start_time": state.timestamp,
                "initial_condition": condition,
                "duration_events": 0,
                "worst_condition": condition,
            }

        current_episode["duration_events"] += 1

        if condition == "BOTH_EMPTY":
            current_episode["worst_condition"] = "BOTH_EMPTY"

    elif current_episode is not None:
        current_episode["recovery_index"] = index
        current_episode["recovery_time"] = state.timestamp
        current_episode["recovered"] = True
        episodes.append(current_episode)
        current_episode = None

# Episode yang belum pulih pada akhir simulasi.
if current_episode is not None:
    current_episode["recovery_index"] = None
    current_episode["recovery_time"] = None
    current_episode["recovered"] = False
    episodes.append(current_episode)


print("=== PHASE 20.5.2: LIQUIDITY REPLENISHMENT AUDIT ===")
print(f"Events: {len(states)}")
print(f"Total episodes: {len(episodes)}")

recovered = [e for e in episodes if e["recovered"]]
unrecovered = [e for e in episodes if not e["recovered"]]

print(f"Recovered episodes: {len(recovered)}")
print(f"Unrecovered at end: {len(unrecovered)}")

if episodes:
    print(
        "Recovery rate: "
        f"{len(recovered) / len(episodes):.2%}"
    )

if recovered:
    durations = [e["duration_events"] for e in recovered]

    print("\n--- Recovered episode duration ---")
    print(f"Mean: {mean(durations):.2f} events")
    print(f"Median: {median(durations):.2f} events")
    print(f"Minimum: {min(durations)} events")
    print(f"Maximum: {max(durations)} events")

    for threshold in (1, 2, 5, 10, 20, 50):
        count = sum(d <= threshold for d in durations)
        print(
            f"Recovered within {threshold:2d} events: "
            f"{count} ({count / len(durations):.2%})"
        )

print("\n--- By initial empty-book condition ---")

grouped = defaultdict(list)
for episode in episodes:
    grouped[episode["initial_condition"]].append(episode)

for condition in ("BID_EMPTY", "ASK_EMPTY", "BOTH_EMPTY"):
    group = grouped[condition]
    group_recovered = [e for e in group if e["recovered"]]

    print(f"\n{condition}")
    print(f"Total episodes: {len(group)}")
    print(f"Recovered: {len(group_recovered)}")
    print(f"Unrecovered: {len(group) - len(group_recovered)}")

    if group_recovered:
        durations = [
            e["duration_events"] for e in group_recovered
        ]
        print(f"Mean recovery duration: {mean(durations):.2f}")
        print(f"Median recovery duration: {median(durations):.2f}")

print("\n--- Longest episodes ---")
for episode in sorted(
    episodes,
    key=lambda e: e["duration_events"],
    reverse=True,
)[:10]:
    print(
        f"start={episode['start_index']}, "
        f"initial={episode['initial_condition']}, "
        f"duration={episode['duration_events']}, "
        f"recovered={episode['recovered']}, "
        f"worst={episode['worst_condition']}"
    )

print("\n--- Final state ---")
print(f"Best bid: {simulation.book.best_bid}")
print(f"Best ask: {simulation.book.best_ask}")
print(f"Active orders: {len(simulation.book.order_index)}")
