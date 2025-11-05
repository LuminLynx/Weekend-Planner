
def budget_aware_score(base_score: float, landed_cost: float, user_budget_pp: float,
                       price_drop_prob_7d: float, days_to_event: int, dining_est_pp: float=0.0,
                       is_bookable: bool=True, user_preferences: dict=None, 
                       event_city: str=None, dining_cuisines: list=None) -> float:
    """
    Calculate score preferring within-budget and bookable options.
    
    Scoring factors:
    - Budget penalty: heavy penalty for over-budget items
    - Bookability bonus: prefer items that are immediately bookable
    - Price drop bonus: reward likely price drops for far-out events
    - Total cost penalty: small penalty for absolute cost
    - Personalization bonus: small bonuses for matching user preferences
    
    Args:
        user_preferences: Optional dict with home_city, preferred_cuisines
        event_city: City where event takes place
        dining_cuisines: List of cuisine types for dining option
    
    Returns:
        Score rounded to 3 decimal places
    """
    total_cost = landed_cost + (dining_est_pp or 0.0)
    
    # Heavy penalty for over-budget (prioritize within-budget)
    budget_gap = max(0.0, landed_cost - user_budget_pp)
    if budget_gap > 0:
        budget_penalty = min(0.8, budget_gap / 25.0)  # Increased from /50 to penalize harder
    else:
        # Bonus for being under budget
        budget_penalty = -(min(0.2, (user_budget_pp - landed_cost) / 100.0))
    
    # Bookability bonus
    bookable_bonus = 0.1 if is_bookable else 0.0
    
    # Price drop bonus (only for far-out events)
    drop_bonus = 0.15 if (price_drop_prob_7d >= 0.4 and days_to_event >= 5) else 0.0
    
    # Small penalty for absolute cost
    cost_penalty = total_cost / 1000.0
    
    # Personalization bonuses
    personalization_bonus = 0.0
    if user_preferences:
        # Bonus if event is near home city
        if event_city and user_preferences.get("home_city"):
            if event_city.lower() == user_preferences["home_city"].lower():
                personalization_bonus += 0.05
        
        # Bonus if dining matches preferred cuisines
        if dining_cuisines and user_preferences.get("preferred_cuisines"):
            preferred = [c.lower() for c in user_preferences["preferred_cuisines"]]
            cuisines = [c.lower() for c in dining_cuisines]
            if any(c in preferred for c in cuisines):
                personalization_bonus += 0.05
    
    score = base_score - budget_penalty + bookable_bonus - cost_penalty + drop_bonus + personalization_bonus
    return round(score, 3)

