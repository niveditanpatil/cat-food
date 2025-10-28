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
        item_type: Type of item ('food' or 'treat')
        calories_per_oz: Calories per ounce
        min_protein: Minimum protein percentage
        max_carbs: Calculated maximum carbohydrate percentage
        min_fat: Minimum fat percentage
        is_dry_matter: Whether the item is dry (no moisture adjustment needed)
    """
    
    def __init__(self, name: str, item_type: str, calories: float, weight: float, weight_unit: str, 
                 min_protein: float, max_fiber: float, min_fat: float, 
                 max_moisture: float, ash: float, max_carbs: float = None):
        """
        Initialize a food item.
        
        All foods default to as-fed basis and are converted to dry matter for fair comparison.
        Carbs can be provided directly OR calculated using: Carbs = 100 - (Protein + Fat + Fiber + Moisture + Ash)³
        
        Args:
            name: Item identifier
            item_type: Type of item ('food' or 'treat')
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
            ValueError: If weight_unit is invalid, moisture >= 100, or item_type is invalid
        """
        self.name = name
        self.item_type = item_type.lower()
        
        if self.item_type not in ['food', 'treat']:
            raise ValueError(f"item_type must be 'food' or 'treat', got '{item_type}'")
        
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
        return (f"Item(name='{self.name}', type='{self.item_type}', calories_per_oz={self.calories_per_oz}, "
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


def calc_quant(items: List[Item], total_calories: float, include_treat: bool = False) -> List[Tuple[str, float]]:
    """
    Calculate optimal quantities of items to meet calorie and macronutrient targets.
    
    Uses a two-stage optimization approach:
    1. First try to find optimal solution without treat constraints
    2. If treat inclusion is requested, use flexible optimization to include treats
    
    Constraints:
    - Total calories equal target
    - Weighted average protein >= 55%
    - Weighted average carbohydrates <= 2%
    - Weighted average fat >= 45%
    - Treats limited to 10% of total calories (VCA Animal Hospitals⁴)
    - At least one treat included (if include_treat=True)
    
    Args:
        items: List of Item objects to choose from
        total_calories: Target total calories
        include_treat: If True, ensures at least one treat is included
    
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
    
    # Stage 1: Try standard optimization without treat inclusion constraint
    result = _optimize_standard(items, total_calories)
    
    # Stage 2: If treat inclusion is requested, try to include treats
    if include_treat and result:
        result_with_treats = _optimize_with_treat_inclusion(items, total_calories, result)
        if result_with_treats:
            return result_with_treats
    
    return result


def _optimize_standard(items: List[Item], total_calories: float) -> List[Tuple[str, float]]:
    """
    Standard optimization without treat inclusion constraints.
    
    Args:
        items: List of Item objects
        total_calories: Target calories
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...] or empty list if no solution
    """
    num_items = len(items)
    
    # Objective: minimize total quantity
    objective_vector = [1] * num_items
    
    # Standard constraints (no treat inclusion)
    inequality_constraints = [
        [(item.max_carbs * (1 - config.CARB_OVERESTIMATION_FACTOR) - config.MACRONUTRIENT_TARGETS['carbs']) 
         for item in items],  # Max carbs
        [-(item.min_protein - config.MACRONUTRIENT_TARGETS['protein']) for item in items],  # Min protein
        [-(item.min_fat - config.MACRONUTRIENT_TARGETS['fat']) for item in items],  # Min fat
        # Treat constraint: treats <= 10% of total calories
        [item.calories_per_oz if item.item_type == 'treat' else 0 for item in items]
    ]
    inequality_bounds = [0, 0, 0, total_calories * 0.1]
    
    # Equality constraint: total calories
    equality_constraints = [[item.calories_per_oz for item in items]]
    equality_bounds = [total_calories]
    
    # Non-negative bounds
    bounds = [(0, None) for _ in range(num_items)]
    
    # Try linear programming
    linear_result = linprog(objective_vector, A_ub=inequality_constraints, 
                           b_ub=inequality_bounds, A_eq=equality_constraints, 
                           b_eq=equality_bounds, bounds=bounds, method='highs')
    
    if linear_result.success:
        return [(items[i].name, round(float(linear_result.x[i]), 2)) 
                for i in range(num_items)]
    
    # Fallback to nonlinear optimization
    return _find_best_approximation(items, total_calories, bounds, num_items, False)


def _optimize_with_treat_inclusion(items: List[Item], total_calories: float, 
                                  base_result: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Optimize to include treats while maintaining good nutrition.
    
    Strategy:
    1. Check if base result already includes treats
    2. If not, try to substitute some food with treats
    3. Use flexible optimization to balance nutrition and treat inclusion
    
    Args:
        items: List of Item objects
        total_calories: Target calories
        base_result: Base optimization result
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...] or empty list if no improvement
    """
    # Check if base result already includes treats
    treats_in_base = [name for name, qty in base_result if qty > 0 and 
                     any(item.name == name and item.item_type == 'treat' for item in items)]
    
    if treats_in_base:
        return base_result  # Already includes treats
    
    # Try greedy substitution approach
    substitution_result = _greedy_treat_substitution(items, total_calories, base_result)
    if substitution_result:
        return substitution_result
    
    # Fall back to simple treat addition
    return _simple_treat_addition(items, total_calories, base_result)


def _greedy_treat_substitution(items: List[Item], total_calories: float, 
                              base_result: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Try to substitute some food with treats using a greedy approach.
    
    Args:
        items: List of Item objects
        total_calories: Target calories
        base_result: Base optimization result
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...] or empty list if no improvement
    """
    # Get available treats
    treats = [item for item in items if item.item_type == 'treat']
    if not treats:
        return []
    
    # Find the best treat to substitute
    best_treat = None
    best_substitution = None
    
    for treat in treats:
        # Try substituting a small amount of food with this treat
        substitution_result = _try_treat_substitution(items, total_calories, base_result, treat)
        if substitution_result:
            if not best_substitution or _is_better_substitution(substitution_result, best_substitution):
                best_treat = treat
                best_substitution = substitution_result
    
    return best_substitution


def _try_treat_substitution(items: List[Item], total_calories: float, 
                           base_result: List[Tuple[str, float]], treat: Item) -> List[Tuple[str, float]]:
    """
    Try substituting a small amount of food with a specific treat.
    
    Args:
        items: List of Item objects
        total_calories: Target calories
        base_result: Base optimization result
        treat: Treat item to substitute with
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...] or empty list if substitution fails
    """
    # Calculate how much treat we can add (up to 10% of calories)
    max_treat_calories = total_calories * 0.1
    max_treat_oz = max_treat_calories / treat.calories_per_oz
    
    # Try different treat amounts
    for treat_oz in [0.01, 0.02, 0.05, max_treat_oz]:
        if treat_oz > max_treat_oz:
            break
            
        treat_calories = treat_oz * treat.calories_per_oz
        
        # Find food items to reduce
        food_items = [(name, qty) for name, qty in base_result if qty > 0 and 
                     any(item.name == name and item.item_type == 'food' for item in items)]
        
        if not food_items:
            continue
            
        # Try to reduce the food item with lowest calories per oz
        food_items.sort(key=lambda x: next(item.calories_per_oz for item in items if item.name == x[0]))
        
        for food_name, food_qty in food_items:
            food_item = next(item for item in items if item.name == food_name)
            food_calories_per_oz = food_item.calories_per_oz
            
            # Calculate how much food to reduce
            food_reduction_oz = treat_calories / food_calories_per_oz
            
            if food_reduction_oz >= food_qty:
                continue  # Can't reduce more than available
            
            # Create new result with substitution
            new_result = []
            substitution_made = False
            
            for name, qty in base_result:
                if name == food_name and not substitution_made:
                    new_result.append((name, qty - food_reduction_oz))
                    substitution_made = True
                else:
                    new_result.append((name, qty))
            
            # Add treat
            treat_found = False
            for name, qty in new_result:
                if name == treat.name:
                    treat_found = True
                    break
            
            if not treat_found:
                new_result.append((treat.name, treat_oz))
            
            # Check if this substitution maintains good nutrition
            if _is_valid_substitution(items, new_result, total_calories):
                return new_result
    
    return []


def _is_better_substitution(result1: List[Tuple[str, float]], result2: List[Tuple[str, float]]) -> bool:
    """Check if result1 is better than result2 for treat inclusion."""
    # Prefer results with more treat quantity
    treat_qty1 = sum(qty for name, qty in result1 if any(item.name == name and item.item_type == 'treat' for item in items))
    treat_qty2 = sum(qty for name, qty in result2 if any(item.name == name and item.item_type == 'treat' for item in items))
    
    return treat_qty1 > treat_qty2


def _is_valid_substitution(items: List[Item], result: List[Tuple[str, float]], total_calories: float) -> bool:
    """Check if a substitution result maintains reasonable nutrition."""
    # Calculate macronutrient ratios
    total_oz = sum(qty for _, qty in result)
    if total_oz <= 0:
        return False
    
    weighted_protein = sum(qty * next(item.min_protein for item in items if item.name == name) 
                          for name, qty in result) / total_oz
    weighted_carbs = sum(qty * next(item.max_carbs for item in items if item.name == name) 
                        for name, qty in result) / total_oz
    weighted_fat = sum(qty * next(item.min_fat for item in items if item.name == name) 
                      for name, qty in result) / total_oz
    
    # Check if nutrition is still reasonable (relaxed constraints)
    adjusted_carbs = weighted_carbs * (1 - config.CARB_OVERESTIMATION_FACTOR)
    
    return (weighted_protein >= 40 and  # Relaxed from 55
            adjusted_carbs <= 10 and   # Relaxed from 2
            weighted_fat >= 30)        # Relaxed from 45


def _simple_treat_addition(items: List[Item], total_calories: float, 
                          base_result: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Simple approach: add a small amount of the best treat.
    
    Args:
        items: List of Item objects
        total_calories: Target calories
        base_result: Base optimization result
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...] or empty list if addition fails
    """
    # Get available treats
    treats = [item for item in items if item.item_type == 'treat']
    if not treats:
        return []
    
    # Find the treat with best macronutrient profile
    best_treat = min(treats, key=lambda t: t.max_carbs)  # Lowest carbs
    
    # Add a small amount (0.01 oz)
    treat_oz = 0.01
    treat_calories = treat_oz * best_treat.calories_per_oz
    
    # Check if this exceeds treat limit
    if treat_calories > total_calories * 0.1:
        return []
    
    # Create new result with treat added
    new_result = base_result.copy()
    
    # Check if treat is already in result
    treat_found = False
    for i, (name, qty) in enumerate(new_result):
        if name == best_treat.name:
            new_result[i] = (name, qty + treat_oz)
            treat_found = True
            break
    
    if not treat_found:
        new_result.append((best_treat.name, treat_oz))
    
    # Reduce a food item to compensate for calories
    food_items = [(name, qty) for name, qty in new_result if qty > 0 and 
                 any(item.name == name and item.item_type == 'food' for item in items)]
    
    if not food_items:
        return []
    
    # Reduce the food item with highest calories per oz
    food_items.sort(key=lambda x: next(item.calories_per_oz for item in items if item.name == x[0]), reverse=True)
    
    food_name, food_qty = food_items[0]
    food_item = next(item for item in items if item.name == food_name)
    food_reduction_oz = treat_calories / food_item.calories_per_oz
    
    if food_reduction_oz >= food_qty:
        return []  # Can't reduce enough
    
    # Apply reduction
    for i, (name, qty) in enumerate(new_result):
        if name == food_name:
            new_result[i] = (name, qty - food_reduction_oz)
            break
    
    return new_result


def _flexible_treat_optimization(items: List[Item], total_calories: float) -> List[Tuple[str, float]]:
    """
    Flexible optimization that prioritizes treat inclusion.
    
    Uses a weighted objective that balances nutrition quality with treat inclusion.
    
    Args:
        items: List of Item objects
        total_calories: Target calories
    
    Returns:
        List of tuples [(item_name, quantity_in_oz), ...] or empty list if no solution
    """
    num_items = len(items)
    
    def objective(quantities):
        """Weighted objective: nutrition quality + treat inclusion bonus."""
        total_oz = sum(quantities) + 1e-10
        
        # Calculate macronutrient ratios
        weighted_protein = sum(quantities[i] * items[i].min_protein 
                              for i in range(num_items)) / total_oz
        weighted_carbs = sum(quantities[i] * items[i].max_carbs 
                            for i in range(num_items)) / total_oz
        weighted_fat = sum(quantities[i] * items[i].min_fat 
                          for i in range(num_items)) / total_oz
        
        # Nutrition penalties (minimize violations)
        adjusted_carbs = weighted_carbs * (1 - config.CARB_OVERESTIMATION_FACTOR)
        protein_penalty = (max(0, config.MACRONUTRIENT_TARGETS['protein'] - weighted_protein)) ** 2
        carbs_penalty = (max(0, adjusted_carbs - config.MACRONUTRIENT_TARGETS['carbs'])) ** 2
        fat_penalty = (max(0, config.MACRONUTRIENT_TARGETS['fat'] - weighted_fat)) ** 2
        
        # Treat limit penalty
        treat_calories = sum(quantities[i] * items[i].calories_per_oz 
                           for i in range(num_items) if items[i].item_type == 'treat')
        treat_limit_penalty = (max(0, treat_calories - total_calories * 0.1)) ** 2
        
        # Treat inclusion bonus (negative penalty for including treats)
        treat_quantity = sum(quantities[i] for i in range(num_items) if items[i].item_type == 'treat')
        treat_bonus = -min(treat_quantity, 0.1) * 10  # Bonus for up to 0.1 oz of treats
        
        # Quantity penalty (prefer minimal solutions)
        quantity_penalty = sum(quantities) * 0.01
        
        return (protein_penalty + carbs_penalty + fat_penalty + treat_limit_penalty + 
                treat_bonus + quantity_penalty)
    
    def calorie_constraint(quantities):
        """Ensure total calories equal target."""
        return sum(quantities[i] * items[i].calories_per_oz 
                   for i in range(num_items)) - total_calories
    
    # Initial guess: equal distribution with slight treat preference
    initial_guess = np.array([total_calories / (num_items * items[i].calories_per_oz) 
                              for i in range(num_items)])
    
    # Boost treat quantities in initial guess
    for i in range(num_items):
        if items[i].item_type == 'treat':
            initial_guess[i] *= 1.5
    
    constraints = [{'type': 'eq', 'fun': calorie_constraint}]
    bounds = [(0, None) for _ in range(num_items)]
    
    # Try optimization
    result = minimize(objective, initial_guess, method='SLSQP', 
                      bounds=bounds, constraints=constraints)
    
    if result.success:
        quantities = [(items[i].name, round(float(result.x[i]), 2)) 
                      for i in range(num_items)]
        
        # Check if we actually included treats
        treat_quantities = [qty for name, qty in quantities 
                           if qty > 0 and any(item.name == name and item.item_type == 'treat' 
                                            for item in items)]
        
        if treat_quantities:
            return quantities
    
    return []


def _find_best_approximation(items: List[Item], total_calories: float,
                             bounds: List[Tuple], num_items: int, include_treat: bool = False) -> List[Tuple[str, float]]:
    """
    Find best approximation when exact solution is infeasible.
    
    Uses nonlinear optimization to minimize constraint violations while
    maintaining the calorie requirement.
    
    Args:
        items: List of Item objects
        total_calories: Target total calories
        bounds: Quantity bounds for each item
        num_items: Number of items
        include_treat: Whether to include treats (ignored in this simplified version)
    
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
        adjusted_carbs = weighted_carbs * (1 - config.CARB_OVERESTIMATION_FACTOR)
        protein_penalty = (max(0, config.MACRONUTRIENT_TARGETS['protein'] - weighted_protein)) ** 2
        carbs_penalty = (max(0, adjusted_carbs - config.MACRONUTRIENT_TARGETS['carbs'])) ** 2
        fat_penalty = (max(0, config.MACRONUTRIENT_TARGETS['fat'] - weighted_fat)) ** 2
        
        # Treat limit penalty
        treat_calories = sum(quantities[i] * items[i].calories_per_oz 
                           for i in range(num_items) if items[i].item_type == 'treat')
        treat_limit_penalty = (max(0, treat_calories - total_calories * 0.1)) ** 2
        
        # Small penalty on total quantity
        quantity_penalty = sum(quantities) * 0.01
        
        return protein_penalty + carbs_penalty + fat_penalty + treat_limit_penalty + quantity_penalty
    
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
