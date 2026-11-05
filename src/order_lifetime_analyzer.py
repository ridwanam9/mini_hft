
from collections import Counter
from statistics import mean, median


class OrderLifetimeAnalyzer:
    """
    Analyze the lifetime of orders that have entered the order book.

    Completed observations:
        - filled
        - cancelled

    Censored observations:
        - active at the end of the simulation
    """

    def __init__(self, order_history, end_time, time_step):
        if time_step <= 0:
            raise ValueError("time_step must be positive")

        self.order_history = order_history
        self.end_time = end_time
        self.time_step = time_step

    def to_event_age(self, start_time, end_time):
        """Convert timestamp difference into event intervals."""
        duration = max(0.0, end_time - start_time)

        return round(duration / self.time_step)

    def collect_observations(self):
        observations = []

        for order_id, record in self.order_history.items():
            entry_time = record.get("book_entry_time")

            # Ignore orders that never entered the order book.
            if entry_time is None:
                continue

            status = record["status"]

            if status in {"filled", "cancelled"}:
                observation_end = record["completion_time"]

                if observation_end is None:
                    continue

                censored = False

            elif status == "active":
                observation_end = self.end_time
                censored = True

            else:
                continue

            lifetime = self.to_event_age(
                entry_time,
                observation_end,
            )

            first_resting_fill_time = record.get(
                "first_resting_fill_time"
            )

            first_fill_age = None

            if first_resting_fill_time is not None:
                first_fill_age = self.to_event_age(
                    entry_time,
                    first_resting_fill_time,
                )

            observations.append({
                "order_id": order_id,
                "status": status,
                "lifetime": lifetime,
                "censored": censored,
                "first_fill_age": first_fill_age,
                "executed_quantity": record["executed_quantity"],
                "remaining_quantity": record["remaining_quantity"],
            })

        return observations

    @staticmethod
    def kaplan_meier(observations, horizons):
        """
        Estimate survival probabilities using Kaplan-Meier.

        An event is a terminal observation:
            filled or cancelled.

        A censored observation is an order still active
        at the end of the simulation.
        """
        if not observations:
            return {horizon: None for horizon in horizons}

        grouped = {}

        for observation in observations:
            duration = observation["lifetime"]

            if duration not in grouped:
                grouped[duration] = {
                    "events": 0,
                    "censored": 0,
                }

            if observation["censored"]:
                grouped[duration]["censored"] += 1
            else:
                grouped[duration]["events"] += 1

        survival = 1.0
        at_risk = len(observations)
        survival_at_horizon = {}

        sorted_times = sorted(grouped)

        for horizon in sorted(horizons):
            for duration in sorted_times:
                if duration > horizon:
                    break

                group = grouped[duration]
                event_count = group["events"]
                censored_count = group["censored"]

                if event_count > 0 and at_risk > 0:
                    survival *= (
                        1 - event_count / at_risk
                    )

                # Remove both events and censored observations
                # after calculating survival at this time.
                at_risk -= event_count + censored_count

            survival_at_horizon[horizon] = survival

            # Only process each duration once.
            sorted_times = [
                duration
                for duration in sorted_times
                if duration > horizon
            ]

        return survival_at_horizon

    def analyze(self):
        observations = self.collect_observations()

        statuses = Counter(
            observation["status"]
            for observation in observations
        )

        completed = [
            observation
            for observation in observations
            if not observation["censored"]
        ]

        filled = [
            observation
            for observation in observations
            if observation["status"] == "filled"
        ]

        cancelled = [
            observation
            for observation in observations
            if observation["status"] == "cancelled"
        ]

        active = [
            observation
            for observation in observations
            if observation["censored"]
        ]

        completed_lifetimes = [
            observation["lifetime"]
            for observation in completed
        ]

        cancellation_ages = [
            observation["lifetime"]
            for observation in cancelled
        ]

        fill_ages = [
            observation["first_fill_age"]
            for observation in observations
            if observation["first_fill_age"] is not None
        ]

        filled_lifetimes = [
            observation["lifetime"]
            for observation in filled
        ]

        horizons = [10, 50, 100, 500]

        survival = self.kaplan_meier(
            observations,
            horizons,
        )

        def average(values):
            return mean(values) if values else None

        def median_value(values):
            return median(values) if values else None

        return {
            "total_resting_orders": len(observations),
            "filled": len(filled),
            "cancelled": len(cancelled),
            "active": len(active),

            "average_lifetime": average(completed_lifetimes),
            "median_lifetime": median_value(completed_lifetimes),

            "average_filled_lifetime": average(filled_lifetimes),
            "median_filled_lifetime": median_value(filled_lifetimes),

            "average_cancellation_age": average(cancellation_ages),
            "median_cancellation_age": median_value(cancellation_ages),

            "average_first_fill_age": average(fill_ages),
            "median_first_fill_age": median_value(fill_ages),

            "survival": survival,
            "observations": observations,
        }
