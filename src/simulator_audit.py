import pandas as pd

from src.simulation import Simulation


def run_audit(num_events=10_000, seed=42):
    simulation = Simulation(
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
        seed=seed,
    )

    states = simulation.run(num_events)

    rows = []

    for state in states:
        rows.append({
            "timestamp": state.timestamp,
            "mid_price": state.mid_price,
            "spread": state.spread,
            "best_bid": state.best_bid,
            "best_ask": state.best_ask,
            "obi": state.obi,
            "ofi": state.ofi,
            "last_trade_price": state.last_trade_price,
            "last_trade_quantity": state.last_trade_quantity,
            "last_trade_aggressor": state.last_trade_aggressor,
        })

    df = pd.DataFrame(rows)

    reference_price = 100.0

    print("\n=== SIMULATOR AUDIT ===")

    print("\n--- PRICE ---")
    print(f"Reference price: {reference_price}")
    print(f"First mid:       {df['mid_price'].iloc[0]}")
    print(f"Last mid:        {df['mid_price'].iloc[-1]}")
    print(f"Min mid:         {df['mid_price'].min()}")
    print(f"Max mid:         {df['mid_price'].max()}")
    print(f"Mean mid:        {df['mid_price'].mean()}")

    distance = df["mid_price"] - reference_price

    print("\n--- DISTANCE FROM REFERENCE ---")
    print(f"Mean distance: {distance.mean()}")
    print(f"Min distance:  {distance.min()}")
    print(f"Max distance:  {distance.max()}")

    print("\n--- SPREAD ---")
    print(f"Mean spread: {df['spread'].mean()}")
    print(f"Min spread:  {df['spread'].min()}")
    print(f"Max spread:  {df['spread'].max()}")

    print("\n--- BOOK POSITION ---")

    bid_distance = df["best_bid"] - reference_price
    ask_distance = df["best_ask"] - reference_price

    print(f"Mean best bid distance: {bid_distance.mean()}")
    print(f"Mean best ask distance: {ask_distance.mean()}")

    print(f"Min best bid distance:  {bid_distance.min()}")
    print(f"Max best bid distance:  {bid_distance.max()}")

    print(f"Min best ask distance:  {ask_distance.min()}")
    print(f"Max best ask distance:  {ask_distance.max()}")

    print("\n--- AGGRESSOR ---")

    aggressor_counts = (
        df["last_trade_aggressor"]
        .value_counts(dropna=False)
    )

    print(aggressor_counts)

    print("\n--- TRADE VOLUME ---")

    trade_volume = (
        df.groupby("last_trade_aggressor")["last_trade_quantity"]
        .sum()
    )

    print(trade_volume)

    print("\n--- OBI ---")
    print(f"Mean OBI: {df['obi'].mean()}")
    print(f"Std OBI:  {df['obi'].std()}")

    print("\n--- EMPTY / MISSING ---")
    print(f"Missing mid:   {df['mid_price'].isna().sum()}")
    print(f"Missing spread:{df['spread'].isna().sum()}")
    print(f"Missing bid:   {df['best_bid'].isna().sum()}")
    print(f"Missing ask:   {df['best_ask'].isna().sum()}")


if __name__ == "__main__":
    run_audit()