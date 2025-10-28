"""
Nutrition optimization module for calculating optimal food quantities.

This module provides functionality to calculate calorie requirements and 
determine optimal food quantities that meet specific macronutrient constraints.
"""

from typing import List, Tuple
from scipy.optimize import linprog, minimize
import numpy as np
import config


class Item:
    """
    Represents a food item with nutritional information.
    
    Attributes:
        name: Item identifier
        calories_per_oz: Calories per ounce
        min_protein: Minimum protein percentage
        max_carbs: Calculated maximum carbohydrate percentage
        min_fat: Minimum fat percentage
        is_dry_matter: Whether the item is dry (no moisture adjustment needed)
    """
    
    def __init__(self, name: str, calories: float, weight: float, weight_unit: str, 
                 min_protein: float, max_fiber: float, min_fat: float, 
                 max_moisture: float, ash: float, max_carbs: float = None):
        """
        Initialize a food item.
        
        All foods default to as-fed basis and are converted to dry matter for fair comparison.
        Carbs can be provided directly OR calculated using: Carbs = 100 - (Protein + Fat + Fiber + Moisture + Ash)³
        
        Args:
            name: Item identifier
            calories: Total calories
            weight: Weight value
            weight_unit: Unit of weight ('oz', 'lb', 'g', 'kg', etc.)
            min_protein: Minimum protein percentage (as-fed from label)
            max_fiber: Maximum fiber percentage (as-fed from label) - not needed if max_carbs provided
            min_fat: Minimum fat percentage (as-fed from label)
            max_moisture: Maximum moisture percentage (as-fed from label, 0 means already dry matter)
            ash: Ash percentage (as-fed from label) - not needed if max_carbs provided
            max_carbs: Optional carb percentage (as-fed from label). If None, will be calculated.
        
        Raises:
            ValueError: If weight_unit is invalid or moisture >= 100
        """
        self.name = name
        
        # Normalize weight unit to lowercase
        weight_unit_lower = weight_unit.lower()
        
        # Convert weight to ounces
        if weight_unit_lower not in config.WEIGHT_CONVERSION:
            raise ValueError(f"Invalid weight unit: {weight_unit}. "
                           f"Supported units: {list(config.WEIGHT_CONVERSION.keys())}")
        
        weight_in_ounces = weight * config.WEIGHT_CONVERSION[weight_unit_lower]
        
        # Calculate calories per oz
        self.calories_per_oz = round(calories / weight_in_ounces, 2)
        
        # Calculate or use provided carbs
        if max_carbs is not None:
            # Use provided carb value (already as-fed)
            carbs_as_fed = max_carbs
        else:
            # Calculate carbs using the PetMD formula: Carbs = 100 - (Protein + Fat + Fiber + Moisture + Ash)³
            carbs_as_fed = 100 - (min_protein + min_fat + max_fiber + max_moisture + ash)
        
        # Convert all nutrients to dry matter basis for fair comparison
        if max_moisture >= 100:
            raise ValueError("Moisture cannot be 100% or greater")
        
        dry_mass = 100 - max_moisture
        
        # If moisture is 0, values are already on dry matter basis (no conversion needed)
        if max_moisture == 0:
            self.min_protein = round(min_protein, 2)
            self.max_carbs = round(carbs_as_fed, 2)
            self.min_fat = round(min_fat, 2)
        else:
            # Convert to dry matter basis
            self.min_protein = round((min_protein / dry_mass) * 100, 2)
            self.max_carbs = round((carbs_as_fed / dry_mass) * 100, 2)
            self.min_fat = round((min_fat / dry_mass) * 100, 2)
    
    def __repr__(self):
        return (f"Item(name='{self.name}', calories_per_oz={self.calories_per_oz}, "
                f"min_protein={self.min_protein}, max_carbs={self.max_carbs}, "
                f"min_fat={self.min_fat})")


def calc_cal(weight_kg: float, activity: int, neutered: bool, meal_count: int) -> float:
    """
    Calculate daily calorie requirement per meal.
    
    Args:
        weight_kg: Body weight in kilograms
        activity: Activity level (1=low, 2=medium, 3=high)
        neutered: Whether neutered (applies 0.8 multiplier)
        meal_count: Number of meals per day
    
    Returns:
        Calories required per meal
    
    Raises:
        KeyError: If activity level is not 1, 2, or 3
    """
    activity_multipliers = {1: 1.2, 2: 1.5, 3: 2}
    
    if activity not in activity_multipliers:
        raise ValueError(f"Activity level must be 1, 2, or 3, got {activity}")
    
    resting_energy_requirement = ((30 * weight_kg) + 70) * activity_multipliers[activity]
    if neutered:
        resting_energy_requirement *= 0.8
    
    return round(resting_energy_requirement / meal_count, 2)


def calc_quant(items: List[Item], total_calories: float) -> List[Tuple[str, float]]:
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
        total_calories: Target total calories
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...]
        Returns empty list if no solution can be found
    
    Raises:
        ValueError: If items list is empty or total_calories <= 0
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    if total_calories <= 0:
        raise ValueError(f"total_calories must be positive, got {total_calories}")
    
    num_items = len(items)
    
    # Objective: minimize total quantity
    objective_vector = [1] * num_items
    
    # Inequality constraints for macronutrient ratios
    # Weighted average by weight: sum(qty * macro) / sum(qty) compared to threshold
    # Reformulated: sum(qty * (macro - threshold)) <= 0 (or >= 0 for minimums)
    # Note: Calculated carbs are overestimated by ~21% due to crude fiber (PetMD³)
    # We adjust the effective carb value downward to account for this
    inequality_constraints = [
        [(item.max_carbs * (1 - config.CARB_OVERESTIMATION_FACTOR) - config.MACRONUTRIENT_TARGETS['carbs']) 
         for item in items],  # Max carbs (adjusted for overestimation)
        [-(item.min_protein - config.MACRONUTRIENT_TARGETS['protein']) for item in items],  # Min protein
        [-(item.min_fat - config.MACRONUTRIENT_TARGETS['fat']) for item in items]  # Min fat
    ]
    inequality_bounds = [0, 0, 0]
    
    # Equality constraint: total calories must equal target
    equality_constraints = [[item.calories_per_oz for item in items]]
    equality_bounds = [total_calories]
    
    # All quantities must be non-negative
    bounds = [(0, None) for _ in range(num_items)]
    
    # Attempt linear programming solution
    linear_result = linprog(objective_vector, A_ub=inequality_constraints, 
                            b_ub=inequality_bounds, A_eq=equality_constraints, 
                            b_eq=equality_bounds, bounds=bounds, method='highs')
    
    if linear_result.success:
        return [(items[i].name, round(float(linear_result.x[i]), 2)) 
                for i in range(num_items)]
    
    # Fallback: find best approximation if exact solution doesn't exist
    return _find_best_approximation(items, total_calories, bounds, num_items)


def _find_best_approximation(items: List[Item], total_calories: float,
                             bounds: List[Tuple], num_items: int) -> List[Tuple[str, float]]:
    """
    Find best approximation when exact solution is infeasible.
    
    Uses nonlinear optimization to minimize constraint violations while
    maintaining the calorie requirement.
    
    Args:
        items: List of Item objects
        total_calories: Target total calories
        bounds: Quantity bounds for each item
        num_items: Number of items
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...]
        Returns empty list if optimization fails
    """
    def objective(quantities):
        """Minimize sum of squared constraint violations."""
        total_oz = sum(quantities) + 1e-10  # Avoid division by zero
        weighted_protein = sum(quantities[i] * items[i].min_protein 
                              for i in range(num_items)) / total_oz
        weighted_carbs = sum(quantities[i] * items[i].max_carbs 
                            for i in range(num_items)) / total_oz
        weighted_fat = sum(quantities[i] * items[i].min_fat 
                          for i in range(num_items)) / total_oz
        
        # Penalize constraint violations
        # Adjust carb value downward by overestimation factor (PetMD³)
        adjusted_carbs = weighted_carbs * (1 - config.CARB_OVERESTIMATION_FACTOR)
        protein_penalty = (max(0, config.MACRONUTRIENT_TARGETS['protein'] - weighted_protein)) ** 2
        carbs_penalty = (max(0, adjusted_carbs - config.MACRONUTRIENT_TARGETS['carbs'])) ** 2
        fat_penalty = (max(0, config.MACRONUTRIENT_TARGETS['fat'] - weighted_fat)) ** 2
        
        # Small penalty on total quantity to prefer minimal solutions
        return protein_penalty + carbs_penalty + fat_penalty + sum(quantities) * 0.01
    
    def calorie_constraint(quantities):
        """Ensure total calories equal target."""
        return sum(quantities[i] * items[i].calories_per_oz 
                   for i in range(num_items)) - total_calories
    
    # Initial guess: equal distribution
    initial_guess = np.array([total_calories / (num_items * items[i].calories_per_oz) 
                              for i in range(num_items)])
    constraints = [{'type': 'eq', 'fun': calorie_constraint}]
    
    nonlinear_result = minimize(objective, initial_guess, method='SLSQP', 
                               bounds=bounds, constraints=constraints)
    
    if nonlinear_result.success:
        return [(items[i].name, round(float(nonlinear_result.x[i]), 2)) 
                for i in range(num_items)]
    
    return []
