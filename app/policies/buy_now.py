
def buy_now_policy(prob: float, days_to_event: int, threshold: float, 
                   min_days_force_buy: int, inventory_hint: str = "med") -> tuple[bool, str]:
    """
    Determine if user should buy now or wait for potential price drop.
    
    Returns:
        (buy_now: bool, reason: str)
    """
    if days_to_event <= min_days_force_buy:
        return True, f"only_{days_to_event}d_left"
    if inventory_hint == "low":
        return True, "low_inventory"
    if prob < threshold:
        return True, f"low_drop_prob_{prob:.2f}"
    return False, f"high_drop_prob_{prob:.2f}_wait"
