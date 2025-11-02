
def budget_aware_score(base_score: float, landed_cost: float, user_budget_pp: float,
                       price_drop_prob_7d: float, days_to_event: int, dining_est_pp: float=0.0) -> float:
    budget_gap = max(0.0, landed_cost - user_budget_pp)
    budget_penalty = min(0.6, budget_gap / 50.0)
    drop_bonus = 0.15 if (price_drop_prob_7d >= 0.4 and days_to_event >= 5) else 0.0
    total_cost = landed_cost + (dining_est_pp or 0.0)
    return float(base_score - budget_penalty - (total_cost / 1000.0) + drop_bonus)
