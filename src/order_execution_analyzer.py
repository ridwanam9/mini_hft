from statistics import mean, median


class OrderExecutionAnalyzer:
    TERMINAL_STATUSES = {"filled", "cancelled"}
    VALID_STATUSES = {"filled", "cancelled", "active"}

    def __init__(self, order_history, end_time, time_step):
        if time_step <= 0:
            raise ValueError("time_step must be positive")

        self.order_history = order_history
        self.end_time = end_time
        self.time_step = time_step

    def to_event_age(self, start_time, end_time):
        duration = max(0.0, end_time - start_time)
        return round(duration / self.time_step)

    def collect_observations(self):
        observations = []

        for order_id, record in self.order_history.items():
            entry_time = record.get("book_entry_time")
            status = record.get("status")

            # Hanya menganalisis order yang pernah masuk order book.
            if entry_time is None:
                continue

            if status not in self.VALID_STATUSES:
                continue

            original_quantity = record["original_quantity"]
            executed_quantity = record["executed_quantity"]
            remaining_quantity = record["remaining_quantity"]

            if original_quantity <= 0:
                continue

            fill_ratio = executed_quantity / original_quantity

            if status == "active":
                observation_end = self.end_time
                censored = True
            else:
                observation_end = record.get("completion_time")

                if observation_end is None:
                    continue

                censored = False

            lifetime = self.to_event_age(
                entry_time,
                observation_end,
            )

            first_fill_time = record.get("first_resting_fill_time")

            first_fill_age = None

            if first_fill_time is not None:
                first_fill_age = self.to_event_age(
                    entry_time,
                    first_fill_time,
                )

            observations.append({
                "order_id": order_id,
                "status": status,
                "original_quantity": original_quantity,
                "executed_quantity": executed_quantity,
                "remaining_quantity": remaining_quantity,
                "fill_ratio": fill_ratio,
                "has_fill": executed_quantity > 0,
                "is_full_fill": (
                    status == "filled"
                    and remaining_quantity == 0
                ),
                "is_partial_fill": (
                    status == "cancelled"
                    and executed_quantity > 0
                ),
                "is_no_fill_cancellation": (
                    status == "cancelled"
                    and executed_quantity == 0
                ),
                "censored": censored,
                "lifetime": lifetime,
                "first_fill_age": first_fill_age,
            })

        return observations

    def analyze(self):
        observations = self.collect_observations()

        completed = [
            obs for obs in observations
            if not obs["censored"]
        ]

        active = [
            obs for obs in observations
            if obs["censored"]
        ]

        filled = [
            obs for obs in completed
            if obs["is_full_fill"]
        ]

        partial_filled = [
            obs for obs in completed
            if obs["is_partial_fill"]
        ]

        no_fill_cancelled = [
            obs for obs in completed
            if obs["is_no_fill_cancellation"]
        ]

        any_filled = [
            obs for obs in completed
            if obs["has_fill"]
        ]

        first_fill_ages = [
            obs["first_fill_age"]
            for obs in observations
            if obs["first_fill_age"] is not None
        ]

        completed_fill_ratios = [
            obs["fill_ratio"]
            for obs in completed
        ]

        all_fill_ratios = [
            obs["fill_ratio"]
            for obs in observations
        ]

        def safe_rate(numerator, denominator):
            if denominator == 0:
                return None

            return numerator / denominator

        def safe_mean(values):
            return mean(values) if values else None

        def safe_median(values):
            return median(values) if values else None

        return {
            "total_resting_orders": len(observations),
            "completed_orders": len(completed),
            "active_orders": len(active),

            "fully_filled": len(filled),
            "partially_filled": len(partial_filled),
            "no_fill_cancelled": len(no_fill_cancelled),
            "any_filled": len(any_filled),

            "any_fill_rate": safe_rate(
                len(any_filled),
                len(completed),
            ),

            "full_fill_rate": safe_rate(
                len(filled),
                len(completed),
            ),

            "partial_fill_rate": safe_rate(
                len(partial_filled),
                len(completed),
            ),

            "no_fill_cancellation_rate": safe_rate(
                len(no_fill_cancelled),
                len(completed),
            ),

            "average_fill_ratio_completed": safe_mean(
                completed_fill_ratios
            ),

            "average_fill_ratio_all": safe_mean(
                all_fill_ratios
            ),

            "average_first_fill_age": safe_mean(
                first_fill_ages
            ),

            "median_first_fill_age": safe_median(
                first_fill_ages
            ),

            "observations": observations,
        }