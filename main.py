"""
Main entry point for the nutrition optimization application.

This module handles I/O operations (loading items from CSV) and provides
the main application entry point.
"""

import csv
from typing import List
import nutrition
import interactive


def load_items_from_csv(csv_file: str) -> List[nutrition.Item]:
    """
    Load items from a CSV file and create Item objects.
    
    CSV format:
    name,type,calories,weight,weight_unit,min_protein,max_fiber,min_fat,max_moisture,ash,max_carbs
    
    - type: 'food' or 'treat' (treats limited to 10% of calories per VCA Animal Hospitals⁴)
    - Carbs can be provided directly in max_carbs column, OR calculated using: Carbs = 100 - (Protein + Fat + Fiber + Moisture + Ash)³
    
    Leave max_carbs empty to calculate from other values.
    Supported weight units: oz, lb, g, kg, and their variations
    
    Args:
        csv_file: Path to the CSV file containing item definitions
    
    Returns:
        List of Item objects
    
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If the CSV format is invalid or required fields are missing
    """
    items = []
    
    try:
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Helper function to safely convert to float or return default
                def safe_float(value, default=None):
                    if value and value.strip():
                        return float(value)
                    return default
                
                item = nutrition.Item(
                    name=row['name'],
                    item_type=row['type'],
                    calories=float(row['calories']),
                    weight=float(row['weight']),
                    weight_unit=row['weight_unit'],
                    min_protein=float(row['min_protein']),
                    max_fiber=safe_float(row.get('max_fiber', ''), 0),
                    min_fat=float(row['min_fat']),
                    max_moisture=float(row['max_moisture']),
                    ash=safe_float(row.get('ash', ''), 0),
                    max_carbs=safe_float(row.get('max_carbs', ''), None)
                )
                items.append(item)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    except KeyError as e:
        raise ValueError(f"Missing required column in CSV: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid value in CSV: {e}")
    
    return items


def load_cat_config(config_file: str = 'cat_config.csv') -> dict:
    """
    Load cat configuration parameters from CSV file.
    
    CSV format:
    parameter,value
    
    Parameters:
    - weight_kg: Body weight in kilograms
    - activity: Activity level (1=low, 2=medium, 3=high)
    - neutered: Whether neutered (True/False)
    - meal_count: Number of meals per day
    
    Args:
        config_file: Path to the CSV file containing cat configuration
    
    Returns:
        Dictionary with configuration parameters
    
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the CSV format is invalid or required parameters are missing
    """
    config = {}
    
    try:
        with open(config_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                param = row['parameter']
                value = row['value']
                
                # Convert parameter types
                if param == 'weight_kg':
                    config[param] = float(value)
                elif param == 'activity':
                    config[param] = int(value)
                elif param == 'neutered':
                    config[param] = value.lower() in ('true', '1', 'yes', 't')
                elif param == 'meal_count':
                    config[param] = int(value)
                else:
                    config[param] = value
                    
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_file}")
    except KeyError as e:
        raise ValueError(f"Missing required column in config CSV: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid value in config CSV: {e}")
    
    return config


def main():
    """Interactive application entry point."""
    try:
        print("🐱 Cat Food Nutrition Optimizer")
        print("=" * 50)
        
        # Load cat configuration
        cat_config = load_cat_config('cat_config.csv')
        
        # Calculate calorie requirement
        total_calories = nutrition.calc_cal(
            weight_kg=cat_config['weight_kg'],
            activity=cat_config['activity'],
            neutered=cat_config['neutered'],
            meal_count=cat_config['meal_count']
        )
        
        print(f"📊 Cat Profile:")
        print(f"   Weight: {cat_config['weight_kg']} kg")
        print(f"   Activity: {cat_config['activity']} ({'Low' if cat_config['activity'] == 1 else 'Medium' if cat_config['activity'] == 2 else 'High'})")
        print(f"   Neutered: {'Yes' if cat_config['neutered'] else 'No'}")
        print(f"   Meals per day: {cat_config['meal_count']}")
        print(f"   Calories per meal: {total_calories}")
        
        # Load all available items
        all_items = load_items_from_csv('food_and_treats.csv')
        
        if not all_items:
            print("❌ No food items found in food_and_treats.csv")
            return
        
        # Get user's item selection
        selected_items = interactive.get_user_selection(all_items)
        
        if not selected_items:
            print("❌ No items selected. Exiting.")
            return
        
        # Get treat preference (only if treats are available in selection)
        treats_in_selection = [item for item in selected_items if item.item_type == 'treat']
        if treats_in_selection:
            include_treat = interactive.get_treat_preference()
        else:
            include_treat = False
            print("\n✓ No treats selected - optimizing purely for nutrition.")
        
        # Confirm calculation
        if not interactive.confirm_calculation(total_calories, selected_items, include_treat):
            print("❌ Calculation cancelled.")
            return
        
        # Calculate optimal quantities
        print("\n🔄 Calculating optimal quantities...")
        results = nutrition.calc_quant(selected_items, total_calories, include_treat)
        
        # Display results
        interactive.display_results(results, total_calories, selected_items)
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main_non_interactive():
    """Non-interactive mode for automated use."""
    # Load cat configuration
    cat_config = load_cat_config('cat_config.csv')
    
    # Calculate calorie requirement
    total_calories = nutrition.calc_cal(
        weight_kg=cat_config['weight_kg'],
        activity=cat_config['activity'],
        neutered=cat_config['neutered'],
        meal_count=cat_config['meal_count']
    )
    print(f"Total calories needed: {total_calories}\n")
    
    # Load items from CSV
    items = load_items_from_csv('food_and_treats.csv')
    
    # Calculate optimal quantities
    result = nutrition.calc_quant(items, total_calories)
    print(f"Result: {result}")


if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--non-interactive":
        main_non_interactive()
    else:
        main()
