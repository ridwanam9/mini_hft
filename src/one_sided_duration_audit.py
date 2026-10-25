from src.simulation import Simulation


def get_book_state(book):
    has_bid = bool(book.bids)
    has_ask = bool(book.asks)

    if has_bid and has_ask:
        return "both_present"
    elif not has_bid and has_ask:
        return "bid_empty"
    elif has_bid and not has_ask:
        return "ask_empty"
    else:
        return "both_empty"


def run_audit(num_events=10_000, seed=42):
    simulation = Simulation(seed=seed)

    current_state = None
    state_start_event = None

    durations = {
        "bid_empty": [],
        "ask_empty": [],
        "both_empty": [],
    }

    state_transitions = []

    for event_number in range(num_events):
        order = simulation.market.generate_order()

        # Kondisi BEFORE event
        previous_book = simulation.book.snapshot()
        state = get_book_state(previous_book)

        # Mulai regime baru
        if state != current_state:

            # Tutup regime sebelumnya
            if current_state in durations:
                duration = event_number - state_start_event

                durations[current_state].append(duration)

            # Catat transition
            if current_state is not None:
                state_transitions.append(
                    (current_state, state)
                )

            current_state = state
            state_start_event = event_number

        simulation.engine.submit_order(order)

    # Tutup regime terakhir
    if current_state in durations:
        duration = num_events - state_start_event
        durations[current_state].append(duration)

    print("=== ONE-SIDED DURATION AUDIT ===")

    print_duration_summary(
        "BID EMPTY",
        durations["bid_empty"],
    )

    print_duration_summary(
        "ASK EMPTY",
        durations["ask_empty"],
    )

    print_duration_summary(
        "BOTH EMPTY",
        durations["both_empty"],
    )

    print("\n--- STATE TRANSITIONS ---")

    for from_state, to_state in state_transitions:
        print(
            f"{format_state(from_state)}"
            f" -> "
            f"{format_state(to_state)}"
        )


def print_duration_summary(name, durations):
    print(f"\n--- {name} ---")

    if not durations:
        print("episodes: 0")
        return

    print(f"episodes: {len(durations)}")

    print(
        f"avg duration: "
        f"{sum(durations) / len(durations):.2f} events"
    )

    sorted_durations = sorted(durations)

    median = sorted_durations[len(sorted_durations) // 2]

    print(
        f"median duration: "
        f"{median:.2f} events"
    )

    print(
        f"min duration: "
        f"{min(durations)} events"
    )

    print(
        f"max duration: "
        f"{max(durations)} events"
    )

    for threshold in [1, 2, 5, 10, 20, 50]:
        count = sum(
            duration >= threshold
            for duration in durations
        )

        percentage = count / len(durations)

        print(
            f">= {threshold:2d} events: "
            f"{count:4d} "
            f"({percentage:.2%})"
        )


def format_state(state):
    names = {
        "both_present": "BOTH",
        "bid_empty": "BID EMPTY",
        "ask_empty": "ASK EMPTY",
        "both_empty": "BOTH EMPTY",
    }

    return names[state]


if __name__ == "__main__":
    run_audit()