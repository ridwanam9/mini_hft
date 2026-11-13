
from statistics import mean


class PassiveAggressiveExecutionAnalyzer:
    VALID_STATUSES = {
        "filled",
        "cancelled",
        "active",
        "expired",
    }

    def __init__(self, order_history):
        self.order_history = order_history

    def collect_observations(self):
        observations = []

        for order_id, record in self.order_history.items():
            

            status = record.get("status")

            if status not in self.VALID_STATUSES:
                continue

            original_quantity = record["original_quantity"]
            executed_quantity = record["executed_quantity"]
            remaining_quantity = record["remaining_quantity"]

            aggressive_quantity = record.get(
                "aggressive_executed_quantity", 0
            )
            passive_quantity = record.get(
                "passive_executed_quantity", 0
            )

            if original_quantity <= 0:
                continue

            if min(
                executed_quantity,
                remaining_quantity,
                aggressive_quantity,
                passive_quantity,
            ) < 0:
                raise ValueError("Execution quantities cannot be negative")

            quantity_consistent = (
                executed_quantity
                == aggressive_quantity + passive_quantity
            )

            observations.append({
                "order_id": order_id,
                "status": status,
                "original_quantity": original_quantity,
                "executed_quantity": executed_quantity,
                "remaining_quantity": remaining_quantity,
                "aggressive_executed_quantity": aggressive_quantity,
                "passive_executed_quantity": passive_quantity,

                "aggressive_fill_ratio": (
                    aggressive_quantity / original_quantity
                ),
                "passive_fill_ratio": (
                    passive_quantity / original_quantity
                ),

                "has_aggressive_fill": aggressive_quantity > 0,
                "has_passive_fill": passive_quantity > 0,

                "is_completed": status in {"filled", "cancelled"},
                "is_active": status == "active",

                "quantity_consistent": quantity_consistent,
            })

        return observations

    def analyze(self):
        observations = self.collect_observations()

        completed = [
            obs for obs in observations
            if obs["is_completed"]
        ]

        active = [
            obs for obs in observations
            if obs["is_active"]
        ]

        def summarize(group):
            aggressive_quantities = [
                obs["aggressive_executed_quantity"]
                for obs in group
            ]

            passive_quantities = [
                obs["passive_executed_quantity"]
                for obs in group
            ]

            executed_quantities = [
                obs["executed_quantity"]
                for obs in group
            ]

            aggressive_total = sum(aggressive_quantities)
            passive_total = sum(passive_quantities)
            executed_total = sum(executed_quantities)

            total_orders = len(group)

            def safe_rate(numerator, denominator):
                if denominator == 0:
                    return None
                return numerator / denominator

            def safe_mean(values):
                values = list(values)
                return mean(values) if values else None

            return {
                "total_orders": total_orders,

                "aggressive_orders": sum(
                    obs["has_aggressive_fill"] for obs in group
                ),

                "passive_orders": sum(
                    obs["has_passive_fill"] for obs in group
                ),

                "aggressive_executed_quantity": aggressive_total,
                "passive_executed_quantity": passive_total,
                "total_executed_quantity": executed_total,

                "aggressive_order_rate": safe_rate(
                    sum(obs["has_aggressive_fill"] for obs in group),
                    total_orders,
                ),

                "passive_order_rate": safe_rate(
                    sum(obs["has_passive_fill"] for obs in group),
                    total_orders,
                ),

                "aggressive_execution_share": safe_rate(
                    aggressive_total,
                    executed_total,
                ),

                "passive_execution_share": safe_rate(
                    passive_total,
                    executed_total,
                ),

                "average_aggressive_fill_ratio": safe_mean(
                    obs["aggressive_fill_ratio"] for obs in group
                ),

                "average_passive_fill_ratio": safe_mean(
                    obs["passive_fill_ratio"] for obs in group
                ),

                "quantity_consistency": all(
                    obs["quantity_consistent"] for obs in group
                ),
            }

        return {
            "total_orders": len(observations),
            "completed_orders": len(completed),
            "active_orders": len(active),

            "overall": summarize(observations),
            "completed": summarize(completed),
            "active": summarize(active),

            "observations": observations,
        }
