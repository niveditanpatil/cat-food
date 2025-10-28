"""
Interactive user interface module for cat food nutrition optimizer.

This module handles user input for selecting food items and configuring treat preferences.
"""

from typing import List, Set
import nutrition


def display_items(items: List[nutrition.Item]) -> None:
    """
    Display a numbered list of all available food items and treats.
    
    Args:
        items: List of Item objects to display
    """
    print("\n" + "="*80)
    print("AVAILABLE FOOD ITEMS AND TREATS")
    print("="*80)
    
    foods = [item for item in items if item.item_type == 'food']
    treats = [item for item in items if item.item_type == 'treat']
    
    if foods:
        print(f"\nFOOD ITEMS ({len(foods)} available):")
        print("-" * 50)
        for i, item in enumerate(foods, 1):
            print(f"{i:2d}. {item.name}")
            print(f"    Calories/oz: {item.calories_per_oz}, Protein: {item.min_protein}%, "
                  f"Carbs: {item.max_carbs}%, Fat: {item.min_fat}%")
    
    if treats:
        print(f"\nTREATS ({len(treats)} available):")
        print("-" * 50)
        start_idx = len(foods) + 1
        for i, item in enumerate(treats, start_idx):
            print(f"{i:2d}. {item.name}")
            print(f"    Calories/oz: {item.calories_per_oz}, Protein: {item.min_protein}%, "
                  f"Carbs: {item.max_carbs}%, Fat: {item.min_fat}%")
    
    print("\n" + "="*80)


def get_user_selection(items: List[nutrition.Item]) -> List[nutrition.Item]:
    """
    Get user's selection of items to include in the calculation.
    
    Args:
        items: List of all available Item objects
    
    Returns:
        List of selected Item objects
    
    Raises:
        ValueError: If user input is invalid
    """
    # Create display mapping: display_number -> item
    foods = [item for item in items if item.item_type == 'food']
    treats = [item for item in items if item.item_type == 'treat']
    
    display_to_item = {}
    display_num = 1
    
    # Map foods first
    for item in foods:
        display_to_item[display_num] = item
        display_num += 1
    
    # Map treats second
    for item in treats:
        display_to_item[display_num] = item
        display_num += 1
    
    display_items(items)
    
    print("\nSELECTION INSTRUCTIONS:")
    print("- Enter the numbers of items you want to include (e.g., '1,3,5' or '1 3 5')")
    print("- You can select any combination of food items and treats")
    print("- Press Enter with no input to select all items")
    
    while True:
        try:
            user_input = input("\nEnter item numbers: ").strip()
            
            if not user_input:
                # Select all items if no input
                print("Selected all items.")
                return items
            
            # Parse user input
            if ',' in user_input:
                indices = [int(x.strip()) for x in user_input.split(',')]
            else:
                indices = [int(x.strip()) for x in user_input.split()]
            
            # Validate indices
            if not indices:
                print("Please enter at least one item number.")
                continue
                
            max_display_num = len(foods) + len(treats)
            if any(idx < 1 or idx > max_display_num for idx in indices):
                print(f"Please enter numbers between 1 and {max_display_num}.")
                continue
            
            # Convert display numbers to items
            selected_items = [display_to_item[idx] for idx in indices]
            
            # Display selection summary
            selected_foods = [item for item in selected_items if item.item_type == 'food']
            selected_treats = [item for item in selected_items if item.item_type == 'treat']
            
            print(f"\nSELECTED ITEMS:")
            print(f"- Food items: {len(selected_foods)}")
            print(f"- Treats: {len(selected_treats)}")
            
            if selected_foods:
                print("  Food:", ", ".join([item.name for item in selected_foods]))
            if selected_treats:
                print("  Treats:", ", ".join([item.name for item in selected_treats]))
            
            return selected_items
            
        except ValueError:
            print("Please enter valid numbers separated by commas or spaces.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return []


def get_treat_preference() -> bool:
    """
    Get user's preference for treat inclusion.
    
    Returns:
        True if user wants at least one treat included, False otherwise
    """
    print("\nTREAT PREFERENCE:")
    print("- Would you like to ensure at least one treat is included in the meal?")
    print("- This will prioritize including treats even if it means slightly suboptimal nutrition")
    print("- Default: No (optimize purely for nutrition)")
    
    while True:
        try:
            response = input("\nInclude at least one treat? (y/n): ").strip().lower()
            
            if response in ['y', 'yes']:
                print("✓ At least one treat will be included in the meal.")
                return True
            elif response in ['n', 'no']:
                print("✓ Optimizing purely for nutrition (treats optional).")
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return False


def confirm_calculation(total_calories: float, selected_items: List[nutrition.Item], 
                       include_treat: bool) -> bool:
    """
    Display calculation summary and get user confirmation.
    
    Args:
        total_calories: Target calories for the meal
        selected_items: Items selected for calculation
        include_treat: Whether to include at least one treat
    
    Returns:
        True if user confirms, False otherwise
    """
    print("\n" + "="*80)
    print("CALCULATION SUMMARY")
    print("="*80)
    print(f"Target calories: {total_calories}")
    print(f"Selected items: {len(selected_items)}")
    print(f"Treat preference: {'Include at least one treat' if include_treat else 'Optimize for nutrition'}")
    
    print(f"\nSelected items:")
    for i, item in enumerate(selected_items, 1):
        print(f"{i:2d}. {item.name} ({item.item_type})")
    
    print("\n" + "="*80)
    
    while True:
        try:
            response = input("Proceed with calculation? (y/n): ").strip().lower()
            
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return False


def display_results(results: List[tuple], total_calories: float, selected_items: List[nutrition.Item]) -> None:
    """
    Display the calculation results in a formatted way.
    
    Args:
        results: List of (item_name, quantity) tuples
        total_calories: Target calories
    """
    if not results:
        print("\n❌ No solution found that meets all constraints.")
        print("Try adjusting your selection or treat preferences.")
        return
    
    print("\n" + "="*80)
    print("OPTIMAL MEAL PLAN")
    print("="*80)
    
    total_oz = sum(qty for _, qty in results)
    actual_calories = sum(qty * next(item.calories_per_oz for item in selected_items if item.name == name) 
                        for name, qty in results)
    
    print(f"Target calories: {total_calories}")
    print(f"Actual calories: {actual_calories:.1f}")
    print(f"Total quantity: {total_oz:.2f} oz")
    
    print(f"\nRECOMMENDED AMOUNTS:")
    print("-" * 50)
    
    food_items = []
    treat_items = []
    
    for name, qty in results:
        if qty > 0:
            # Find the item to get its type
            item = next((item for item in selected_items if item.name == name), None)
            if item:
                if item.item_type == 'food':
                    food_items.append((name, qty))
                else:
                    treat_items.append((name, qty))
    
    if food_items:
        print("Food items:")
        for name, qty in food_items:
            print(f"  • {name}: {qty:.2f} oz")
    
    if treat_items:
        print("Treats:")
        for name, qty in treat_items:
            print(f"  • {name}: {qty:.2f} oz")
    
    print("\n" + "="*80)
