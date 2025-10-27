"""
Nutrition optimization module for calculating optimal food quantities.

This module provides functionality to calculate calorie requirements and 
determine optimal food quantities that meet specific macronutrient constraints.
"""

from typing import List, Tuple
from scipy.optimize import linprog, minimize
import numpy as np


# Constants
GRAMS_PER_OZ = 35.274
MACRONUTRIENT_TARGETS = {'pt': 55, 'cb': 2, 'ft': 45}


class Item:
    """
    Represents a food item with nutritional information.
    
    Attributes:
        name: Item identifier
        cal_oz: Calories per ounce
        min_pt: Minimum protein percentage
        max_cb: Maximum carbohydrate percentage
        min_ft: Minimum fat percentage
        dry: Whether the item is dry (no moisture adjustment needed)
    """
    
    def __init__(self, name: str, cal: float, wt: float, oz: bool, dry: bool,
                 min_pt: float, max_cb: float, min_ft: float, max_mt: float = None):
        """
        Initialize a food item.
        
        Args:
            name: Item identifier
            cal: Total calories
            wt: Weight in kg (if oz=False) or oz (if oz=True)
            oz: If True, wt is in oz; if False, wt is in kg
            dry: Whether macronutrients are on dry matter basis
            min_pt: Minimum protein percentage
            max_cb: Maximum carbohydrate percentage
            min_ft: Minimum fat percentage
            max_mt: Maximum moisture percentage (required if dry=False)
        
        Raises:
            ValueError: If dry=False and max_mt is None
        """
        if not dry and max_mt is None:
            raise ValueError("max_mt is required when dry=False")
        
        self.name = name
        
        # Calculate calories per oz
        if oz:
            self.cal_oz = round(cal / wt, 2)
        else:
            self.cal_oz = round(cal / (wt * GRAMS_PER_OZ), 2)
        
        self.dry = dry
        
        # Adjust macronutrient percentages for moisture content
        if not dry:
            dry_mass = 100 - max_mt
            self.min_pt = round((min_pt / dry_mass) * 100, 2)
            self.max_cb = round((max_cb / dry_mass) * 100, 2)
            self.min_ft = round((min_ft / dry_mass) * 100, 2)
        else:
            self.min_pt = round(min_pt, 2)
            self.max_cb = round(max_cb, 2)
            self.min_ft = round(min_ft, 2)
    
    def __repr__(self):
        return (f"Item(name='{self.name}', cal_oz={self.cal_oz}, "
                f"min_pt={self.min_pt}, max_cb={self.max_cb}, min_ft={self.min_ft})")


def calc_cal(weight_kg: float, activity: int, neut: bool, times: int) -> float:
    """
    Calculate daily calorie requirement per meal.
    
    Args:
        weight_kg: Body weight in kilograms
        activity: Activity level (1=low, 2=medium, 3=high)
        neut: Whether neutered (applies 0.8 multiplier)
        times: Number of meals per day
    
    Returns:
        Calories required per meal
    
    Raises:
        KeyError: If activity level is not 1, 2, or 3
    """
    activity_multipliers = {1: 1.2, 2: 1.5, 3: 2}
    
    if activity not in activity_multipliers:
        raise ValueError(f"Activity level must be 1, 2, or 3, got {activity}")
    
    rer = ((30 * weight_kg) + 70) * activity_multipliers[activity]
    if neut:
        rer *= 0.8
    
    return round(rer / times, 2)


def calc_quant(items: List[Item], total_cal: float) -> List[Tuple[str, float]]:
    """
    Calculate optimal quantities of items to meet calorie and macronutrient targets.
    
    Uses linear programming to find quantities that satisfy:
    - Total calories equal target
    - Weighted average protein >= 55%
    - Weighted average carbohydrates <= 2%
    - Weighted average fat >= 45%
    
    If no exact solution exists, uses nonlinear optimization to find the best
    approximation that minimizes constraint violations.
    
    Args:
        items: List of Item objects to choose from
        total_cal: Target total calories
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...]
        Returns empty list if no solution can be found
    
    Raises:
        ValueError: If items list is empty or total_cal <= 0
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    if total_cal <= 0:
        raise ValueError(f"total_cal must be positive, got {total_cal}")
    
    n = len(items)
    
    # Objective: minimize total quantity
    c = [1] * n
    
    # Inequality constraints for macronutrient ratios
    # Weighted average by weight: sum(qty * macro) / sum(qty) compared to threshold
    # Reformulated: sum(qty * (macro - threshold)) <= 0 (or >= 0 for minimums)
    A_ub = [
        [item.max_cb - MACRONUTRIENT_TARGETS['cb'] for item in items],  # Max carbs
        [-(item.min_pt - MACRONUTRIENT_TARGETS['pt']) for item in items],  # Min protein
        [-(item.min_ft - MACRONUTRIENT_TARGETS['ft']) for item in items]  # Min fat
    ]
    b_ub = [0, 0, 0]
    
    # Equality constraint: total calories must equal target
    A_eq = [[item.cal_oz for item in items]]
    b_eq = [total_cal]
    
    # All quantities must be non-negative
    bounds = [(0, None) for _ in range(n)]
    
    # Attempt linear programming solution
    result_opt = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                         bounds=bounds, method='highs')
    
    if result_opt.success:
        return [(items[i].name, round(result_opt.x[i], 2)) for i in range(n)]
    
    # Fallback: find best approximation if exact solution doesn't exist
    return _find_best_approximation(items, total_cal, bounds, n)


def _find_best_approximation(items: List[Item], total_cal: float,
                             bounds: List[Tuple], n: int) -> List[Tuple[str, float]]:
    """
    Find best approximation when exact solution is infeasible.
    
    Uses nonlinear optimization to minimize constraint violations while
    maintaining the calorie requirement.
    
    Args:
        items: List of Item objects
        total_cal: Target total calories
        bounds: Quantity bounds for each item
        n: Number of items
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...]
        Returns empty list if optimization fails
    """
    def objective(x):
        """Minimize sum of squared constraint violations."""
        total_oz = sum(x) + 1e-10  # Avoid division by zero
        weighted_pt = sum(x[i] * items[i].min_pt for i in range(n)) / total_oz
        weighted_cb = sum(x[i] * items[i].max_cb for i in range(n)) / total_oz
        weighted_ft = sum(x[i] * items[i].min_ft for i in range(n)) / total_oz
        
        # Penalize constraint violations
        pt_penalty = max(0, MACRONUTRIENT_TARGETS['pt'] - weighted_pt) ** 2
        cb_penalty = max(0, weighted_cb - MACRONUTRIENT_TARGETS['cb']) ** 2
        ft_penalty = max(0, MACRONUTRIENT_TARGETS['ft'] - weighted_ft) ** 2
        
        # Small penalty on total quantity to prefer minimal solutions
        return pt_penalty + cb_penalty + ft_penalty + sum(x) * 0.01
    
    def cal_constraint(x):
        """Ensure total calories equal target."""
        return sum(x[i] * items[i].cal_oz for i in range(n)) - total_cal
    
    # Initial guess: equal distribution
    x0 = np.array([total_cal / (n * items[i].cal_oz) for i in range(n)])
    constraints = [{'type': 'eq', 'fun': cal_constraint}]
    
    result_approx = minimize(objective, x0, method='SLSQP', bounds=bounds,
                            constraints=constraints)
    
    if result_approx.success:
        return [(items[i].name, round(result_approx.x[i], 2)) for i in range(n)]
    
    return []


def main():
    """Example usage of the nutrition optimization functions."""
    # Calculate calorie requirement
    total_cal = calc_cal(weight_kg=5.5, activity=1, neut=True, times=4)
    print(f"Total calories needed: {total_cal}\n")
    
    # Define items
    item_a = Item(
        name='a',
        cal=407,
        wt=1,
        oz=False,
        dry=False,
        min_pt=10,
        max_cb=1,
        min_ft=5,
        max_mt=78
    )
    item_b = Item(
        name='b',
        cal=4200,
        wt=1,
        oz=False,
        dry=False,
        min_pt=43,
        max_cb=3,
        min_ft=28,
        max_mt=8
    )
    item_c = Item(
        name='c',
        cal=39,
        wt=1,
        oz=True,
        dry=False,
        min_pt=17,
        max_cb=2.2,
        min_ft=7.6,
        max_mt=72
    )
    item_d = Item(
        name='d',
        cal=41,
        wt=1,
        oz=True,
        dry=False,
        min_pt=15.6,
        max_cb=1.7,
        min_ft=7.7,
        max_mt=72
    )
    item_e = Item(
        name='e',
        cal=40,
        wt=1,
        oz=True,
        dry=False,
        min_pt=13,
        max_cb=1.5,
        min_ft=8.5,
        max_mt=73
    )
    item_f = Item(
        name='f',
        cal=3590,
        wt=1,
        oz=False,
        dry=False,
        min_pt=65,
        max_cb=6,
        min_ft=10,
        max_mt=8
    )
    
    # Calculate optimal quantities
    result = calc_quant([item_a, item_b, item_c, item_d, item_e, item_f], total_cal)
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
