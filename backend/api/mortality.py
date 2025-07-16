"""
Mortality table calculations for retirement planning.
Based on Social Security Administration 2019 Period Life Table.
"""

# Simplified mortality rates per 1000 population by age and gender
# Source: SSA 2019 Period Life Table (approximate values)
MORTALITY_RATES = {
    'male': {
        50: 4.8, 51: 5.2, 52: 5.7, 53: 6.2, 54: 6.8, 55: 7.4, 56: 8.1, 57: 8.9, 58: 9.7, 59: 10.6,
        60: 11.6, 61: 12.7, 62: 13.9, 63: 15.2, 64: 16.6, 65: 18.2, 66: 19.9, 67: 21.8, 68: 23.9, 69: 26.2,
        70: 28.8, 71: 31.6, 72: 34.8, 73: 38.3, 74: 42.2, 75: 46.6, 76: 51.5, 77: 57.0, 78: 63.1, 79: 69.9,
        80: 77.5, 81: 86.0, 82: 95.5, 83: 106.2, 84: 118.2, 85: 131.7, 86: 147.0, 87: 164.3, 88: 183.9, 89: 206.1,
        90: 231.4, 91: 260.2, 92: 292.9, 93: 330.1, 94: 372.4, 95: 420.4, 96: 475.0, 97: 537.1, 98: 607.7, 99: 688.0,
        100: 779.2, 101: 882.6, 102: 999.6, 103: 1131.8, 104: 1281.1, 105: 1449.6, 106: 1639.7, 107: 1853.9, 108: 2094.9, 109: 2365.5,
        110: 2669.5, 111: 3010.0, 112: 3390.2, 113: 3814.4, 114: 4287.0, 115: 4812.6, 116: 5396.0, 117: 6042.3, 118: 6756.9, 119: 7546.4, 120: 8417.4
    },
    'female': {
        50: 2.9, 51: 3.2, 52: 3.5, 53: 3.8, 54: 4.2, 55: 4.6, 56: 5.0, 57: 5.5, 58: 6.0, 59: 6.6,
        60: 7.2, 61: 7.9, 62: 8.6, 63: 9.4, 64: 10.3, 65: 11.3, 66: 12.4, 67: 13.6, 68: 14.9, 69: 16.4,
        70: 18.0, 71: 19.8, 72: 21.8, 73: 24.0, 74: 26.4, 75: 29.1, 76: 32.1, 77: 35.5, 78: 39.3, 79: 43.6,
        80: 48.4, 81: 53.8, 82: 59.9, 83: 66.7, 84: 74.4, 85: 83.1, 86: 92.9, 87: 103.9, 88: 116.3, 89: 130.4,
        90: 146.3, 91: 164.3, 92: 184.6, 93: 207.5, 94: 233.4, 95: 262.6, 96: 295.5, 97: 332.7, 98: 374.7, 99: 422.2,
        100: 475.8, 101: 536.3, 102: 604.6, 103: 681.5, 104: 767.9, 105: 864.8, 106: 973.3, 107: 1094.6, 108: 1230.0, 109: 1380.9,
        110: 1548.8, 111: 1735.4, 112: 1942.5, 113: 2171.9, 114: 2425.5, 115: 2705.2, 116: 3013.1, 117: 3351.5, 118: 3722.8, 119: 4129.5, 120: 4574.2
    }
}

def get_mortality_rate(age: int, gender: str) -> float:
    """
    Get mortality rate per 1000 population for given age and gender.
    
    Args:
        age: Age of person
        gender: 'male' or 'female'
    
    Returns:
        Mortality rate per 1000 population
    """
    if age < 50:
        # Very low mortality rates for younger ages
        return 1.0 if gender == 'male' else 0.7
    elif age > 120:
        return 1000.0  # Certain death
    else:
        return MORTALITY_RATES.get(gender, MORTALITY_RATES['male']).get(age, 1000.0)

def calculate_survival_probability(age: int, gender: str, years: int = 1) -> float:
    """
    Calculate probability of surviving the next N years.
    
    Args:
        age: Current age
        gender: 'male' or 'female'
        years: Number of years to calculate survival for
    
    Returns:
        Probability of survival (0.0 to 1.0)
    """
    survival_prob = 1.0
    
    for year in range(years):
        current_age = age + year
        mortality_rate = get_mortality_rate(current_age, gender)
        annual_survival_prob = 1.0 - (mortality_rate / 1000.0)
        survival_prob *= annual_survival_prob
        
        if survival_prob <= 0:
            break
    
    return max(0.0, survival_prob)

def calculate_cumulative_survival_probability(start_age: int, current_age: int, gender: str) -> float:
    """
    Calculate cumulative survival probability from start_age to current_age.
    
    Args:
        start_age: Age at the beginning of projection
        current_age: Current age
        gender: 'male' or 'female'
    
    Returns:
        Probability of surviving from start_age to current_age (0.0 to 1.0)
    """
    if current_age <= start_age:
        return 1.0  # Already at or before start age
    
    years_elapsed = current_age - start_age
    return calculate_survival_probability(start_age, gender, years_elapsed)

def calculate_joint_survival_probability(people: list, years: int = 1) -> dict:
    """
    Calculate survival probabilities for multiple people.
    
    Args:
        people: List of dicts with 'age' and 'gender' keys
        years: Number of years to calculate
    
    Returns:
        Dict with survival probabilities:
        - individual: List of individual survival probabilities
        - at_least_one: Probability at least one person survives
        - both_alive: Probability all people survive (for couples)
        - mortality_95pct: Year when 95% chance both have died
    """
    if not people:
        return {}
    
    individual_probs = []
    
    for person in people:
        prob = calculate_survival_probability(person['age'], person['gender'], years)
        individual_probs.append(prob)
    
    # Probability that at least one person survives
    prob_all_dead = 1.0
    for prob in individual_probs:
        prob_all_dead *= (1.0 - prob)
    at_least_one_alive = 1.0 - prob_all_dead
    
    # Probability that all people survive
    both_alive = 1.0
    for prob in individual_probs:
        both_alive *= prob
    
    # Find year when 95% chance both have died
    mortality_95pct_year = None
    for test_years in range(1, 51):  # Test up to 50 years
        long_term_both_alive = 1.0
        for person in people:
            prob = calculate_survival_probability(person['age'], person['gender'], test_years)
            long_term_both_alive *= prob
        
        if long_term_both_alive <= 0.05:  # 95% chance both dead
            mortality_95pct_year = test_years
            break
    
    return {
        'individual': individual_probs,
        'at_least_one': at_least_one_alive,
        'both_alive': both_alive,
        'mortality_95pct_year': mortality_95pct_year
    }

def get_life_expectancy(age: int, gender: str) -> float:
    """
    Calculate remaining life expectancy from current age.
    
    Args:
        age: Current age
        gender: 'male' or 'female'
    
    Returns:
        Expected remaining years of life
    """
    total_years = 0.0
    
    for year in range(120 - age):
        current_age = age + year
        survival_prob = calculate_survival_probability(current_age, gender, 1)
        total_years += survival_prob
        
        if survival_prob < 0.01:  # Less than 1% chance of surviving another year
            break
    
    return total_years