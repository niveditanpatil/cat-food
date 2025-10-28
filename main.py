"""
Main entry point for the nutrition optimization application.

This module handles I/O operations (loading items from CSV) and provides
the main application entry point.
"""

import csv
from typing import List
import nutrition


def load_items_from_csv(csv_file: str) -> List[nutrition.Item]:
    """
    Load items from a CSV file and create Item objects.
    
    CSV format:
    name,calories,weight,weight_unit,min_protein,max_fiber,min_fat,max_moisture,ash
    
    Carbs are calculated using: Carbs = 100 - (Protein + Fat + Fiber + Moisture + Ash)³
    
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
                item = nutrition.Item(
                    name=row['name'],
                    calories=float(row['calories']),
                    weight=float(row['weight']),
                    weight_unit=row['weight_unit'],
                    min_protein=float(row['min_protein']),
                    max_fiber=float(row['max_fiber']),
                    min_fat=float(row['min_fat']),
                    max_moisture=float(row['max_moisture']),
                    ash=float(row['ash'])
                )
                items.append(item)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    except KeyError as e:
        raise ValueError(f"Missing required column in CSV: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid value in CSV: {e}")
    
    return items


def main():
    """Example usage of the nutrition optimization functions."""
    # Calculate calorie requirement
    total_calories = nutrition.calc_cal(weight_kg=5.5, activity=1, 
                                        neutered=True, meal_count=4)
    print(f"Total calories needed: {total_calories}\n")
    
    # Load items from CSV
    items = load_items_from_csv('items.csv')
    
    # Calculate optimal quantities
    result = nutrition.calc_quant(items, total_calories)
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
