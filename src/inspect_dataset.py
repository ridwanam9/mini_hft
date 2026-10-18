import csv


def inspect_dataset(filepath):

    with open(filepath, newline="") as file:
        rows = list(csv.DictReader(file))

    print("Number of rows:", len(rows))

    if not rows:
        return

    print("\nColumns:")
    for column in rows[0]:
        print("-", column)

    print("\nFirst 5 rows:")

    for row in rows[:5]:
        print(row)


if __name__ == "__main__":
    inspect_dataset(
        "data/market_states.csv"
    )

