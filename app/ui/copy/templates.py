
def itinerary_copy(event_title: str, start_ts: str, landed_amount: float, landed_cur: str,
                   provider: str, price_drop_prob_7d: float, buy_now: bool,
                   dining_name: str|None=None, dining_est_pp: float|None=None) -> str:
    buy_txt = "Buy now" if buy_now else "Might drop—set alert"
    dining_txt = f" | Nearby: {dining_name} (~{dining_est_pp:.0f} {landed_cur} pp)" if dining_name else ""
    return (f"• {event_title} ({start_ts}) — {landed_amount:.2f} {landed_cur} via {provider}. "
            f"{buy_txt} (drop prob {price_drop_prob_7d*100:.0f}%).{dining_txt}")
