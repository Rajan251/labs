import argparse

def calculate_cost(words_per_day, model_wpm=1000, hourly_rate=5.67, spot_rate=2.50, is_priority=False):
    words_per_hour = model_wpm * 60
    processing_hours = words_per_day / words_per_hour
    
    # Add overhead (startup/shutdown) - assume 10 mins per batch if not continuous
    # For simplicity, if processing < 24h, add 20% overhead or min 1 hour
    effective_hours = max(processing_hours * 1.2, 0.5) 
    
    if is_priority:
        # Priority always uses On-Demand and has a minimum of 24h if we keep 1 warm
        # But for per-job cost, let's assume we pay for the capacity we use + warm pool
        # Warm pool cost (1 node 24/7)
        warm_pool_cost = 24 * hourly_rate
        # Extra capacity cost
        burst_cost = max(0, effective_hours - 24) * hourly_rate
        total_cost = warm_pool_cost + burst_cost
        rate_used = hourly_rate
    else:
        # Standard uses Spot and scales to zero
        total_cost = effective_hours * spot_rate
        rate_used = spot_rate
        
    return {
        "words": words_per_day,
        "processing_hours": round(processing_hours, 2),
        "effective_hours": round(effective_hours, 2),
        "rate": rate_used,
        "total_cost_day": round(total_cost, 2),
        "total_cost_month": round(total_cost * 30, 2)
    }

def main():
    scenarios = [
        {"words": 10000, "priority": False},
        {"words": 100000, "priority": False},
        {"words": 1000000, "priority": False},
        {"words": 10000, "priority": True} # Example priority scenario
    ]
    
    print(f"{'Words/Day':<12} | {'Type':<10} | {'Hours':<6} | {'Cost/Day':<10} | {'Cost/Month':<12}")
    print("-" * 65)
    
    for s in scenarios:
        res = calculate_cost(s["words"], is_priority=s["priority"])
        type_str = "Priority" if s["priority"] else "Standard"
        print(f"{res['words']:<12} | {type_str:<10} | {res['effective_hours']:<6} | ${res['total_cost_day']:<9} | ${res['total_cost_month']:<11}")

if __name__ == "__main__":
    main()
