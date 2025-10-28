# Cat Food Nutrition Optimizer

A Python application that calculates optimal food quantities for cats using linear programming to meet specific calorie and macronutrient targets.

## Features

- **Flexible Weight Units**: Accept weights in any unit (oz, lb, g, kg) and converts internally
- **Automatic Conversion**: All weight calculations are normalized to ounces
- **Linear Programming**: Uses scipy.optimize to find optimal quantities meeting:
  - Protein ≥ 55%
  - Carbohydrates ≤ 2%
  - Fat ≥ 45%
  - Treats ≤ 10% of total calories⁴
- **Moisture Adjustment**: Automatically adjusts dry-matter nutritional values for wet foods
- **Treat Management**: Distinguishes between food and treats with automatic calorie limits
- **Interactive Selection**: User-friendly interface for selecting items and preferences
- **CSV Data Management**: Easy-to-edit CSV format for managing food items

## Project Structure

```
cat-food/
├── config.py          # Configuration constants (weight units, macronutrient targets)
├── nutrition.py       # Core business logic (Item class, calculations, optimization)
├── main.py           # Entry point with I/O operations (CSV loading)
├── interactive.py    # Interactive user interface for item selection
├── food_and_treats.csv  # Food and treat item data
├── cat_config.csv    # Cat profile configuration
├── requirements.txt  # Python dependencies
└── venv/            # Virtual environment
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cat-food
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**
   ```bash
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Interactive Mode (Default)

Run the application in interactive mode:
```bash
python main.py
```

The interactive mode provides a user-friendly interface that will:

1. **Display your cat's profile** based on `cat_config.csv`
2. **Show all available food items and treats** from `food_and_treats.csv` in a numbered list
3. **Let you select specific items** by entering their numbers (e.g., "1,3,5" or "1 3 5")
4. **Ask about treat preferences** (include at least one treat or optimize purely for nutrition)
5. **Confirm your selection** before calculating
6. **Calculate optimal quantities** and display formatted results

**Example interaction:**
```
🐱 Cat Food Nutrition Optimizer
==================================================
📊 Cat Profile:
   Weight: 5.5 kg
   Activity: 1 (Low)
   Neutered: Yes
   Meals per day: 4
   Calories per meal: 56.4

================================================================================
AVAILABLE FOOD ITEMS AND TREATS
================================================================================

FOOD ITEMS (3 available):
--------------------------------------------------
 1. Dave's pet food chicken dinner pate
    Calories/oz: 35.28, Protein: 40.91%, Carbs: 4.55%, Fat: 29.55%

 2. Vital essentials freeze dried raw duck entree nibs
    Calories/oz: 148.15, Protein: 50.53%, Carbs: 2.11%, Fat: 22.11%

 3. Tikicat after dark chicken quail and chicken liver recipe in broth
    Calories/oz: 28.25, Protein: 58.82%, Carbs: 4.71%, Fat: 11.76%

TREATS (2 available):
--------------------------------------------------
 4. Bonkers purrpops chicky licks
    Calories/oz: 160.14, Protein: 63.83%, Carbs: 1.28%, Fat: 22.34%

 5. Choolip berry good milk
    Calories/oz: 23.37, Protein: 25.00%, Carbs: 0.00%, Fat: 25.00%

SELECTION INSTRUCTIONS:
- Enter the numbers of items you want to include (e.g., '1,3,5' or '1 3 5')
- You can select any combination of food items and treats
- Press Enter with no input to select all items

Enter item numbers: 1,3,4

SELECTED ITEMS:
- Food items: 2
- Treats: 1
  Food: Dave's pet food chicken dinner pate, Tikicat after dark chicken quail and chicken liver recipe in broth
  Treats: Bonkers purrpops chicky licks

TREAT PREFERENCE:
- Would you like to ensure at least one treat is included in the meal?
- This will prioritize including treats even if it means slightly suboptimal nutrition
- Default: No (optimize purely for nutrition)

Include at least one treat? (y/n): y
✓ At least one treat will be included in the meal.

================================================================================
CALCULATION SUMMARY
================================================================================
Target calories: 56.4
Selected items: 3
Treat preference: Include at least one treat

Selected items:
 1. Dave's pet food chicken dinner pate (food)
 2. Tikicat after dark chicken quail and chicken liver recipe in broth (food)
 3. Bonkers purrpops chicky licks (treat)

================================================================================
Proceed with calculation? (y/n): y

🔄 Calculating optimal quantities...

================================================================================
OPTIMAL MEAL PLAN
================================================================================
Target calories: 56.4
Actual calories: 56.4
Total quantity: 0.36 oz

RECOMMENDED AMOUNTS:
--------------------------------------------------
Food items:
  • Dave's pet food chicken dinner pate: 0.20 oz
  • Tikicat after dark chicken quail and chicken liver recipe in broth: 0.00 oz
Treats:
  • Bonkers purrpops chicky licks: 0.16 oz

================================================================================
```

### Non-Interactive Mode

For automated use or scripting, use the `--non-interactive` flag:

```bash
python main.py --non-interactive
```

This mode will:
- Use all items from `food_and_treats.csv`
- Use default treat preferences (no forced treat inclusion)
- Output results in a simple format

### Configuring Your Cat's Profile

Edit `cat_config.csv` to set your cat's parameters:

```csv
parameter,value
weight_kg,5.5
activity,1
neutered,True
meal_count,4
```

**Parameters:**
- `weight_kg`: Your cat's weight in kilograms
- `activity`: Activity level (1=low/sedentary, 2=medium, 3=high/very active)
- `neutered`: Whether your cat is neutered (`True` or `False`)
- `meal_count`: Number of meals per day

Edit `cat_config.csv` to set your cat's profile:
```csv
parameter,value
weight_kg,5.5
activity,1
neutered,True
meal_count,4
```

**Parameters:**
- `weight_kg`: Your cat's weight in kilograms
- `activity`: Activity level (1=low/sedentary, 2=medium, 3=high/very active)
- `neutered`: Whether your cat is neutered (`True` or `False`)
- `meal_count`: Number of meals per day

### Adding Food Items and Treats

Edit `food_and_treats.csv` to add or modify food items and treats:

```csv
name,type,calories,weight,weight_unit,min_protein,max_fiber,min_fat,max_moisture,ash,max_carbs
```

**Columns:**
- `name`: Item identifier (e.g., "chicken", "salmon")
- `type`: Item type ('food' or 'treat') - treats limited to 10% of calories⁴
- `calories`: Total calories in the given weight
- `weight`: Weight value
- `weight_unit`: Unit of measurement (`oz`, `lb`, `g`, `kg`, `grams`, etc.)
- `min_protein`: Protein percentage from label (as-fed)
- `max_fiber`: Fiber percentage from label (as-fed)
- `min_fat`: Fat percentage from label (as-fed)
- `max_moisture`: Moisture percentage from label (as-fed, 0 means already dry matter)
- `ash`: Ash percentage (as-fed) - typically 3% for canned food, 6% for dry food³
- `max_carbs`: **Optional** - Direct carb percentage from label (as-fed). If empty, calculated from other values.

**Carbohydrate Options:**
1. **Provide directly:** Enter carb percentage in `max_carbs` column
2. **Auto-calculate:** Leave `max_carbs` empty, carbs calculated using:³
```
Carbs = 100 - (Protein + Fat + Fiber + Moisture + Ash)
```

**Dry Matter Conversion:**
All label values are automatically converted to dry matter basis for fair comparison.⁴

**Supported Weight Units:**
- `oz`, `ozs`, `ounce`, `ounces` - Ounces
- `lb`, `lbs`, `pound`, `pounds` - Pounds
- `g`, `gram`, `grams` - Grams
- `kg`, `kilogram`, `kilograms`, `kilo` - Kilograms

**Example:**
```csv
name,type,calories,weight,weight_unit,min_protein,max_fiber,min_fat,max_moisture,ash,max_carbs
chicken_pate,food,100,3,oz,10,1.5,5,78,3,
salmon_kibble,food,400,100,grams,35,2.5,15,8,6,
cat_treat,treat,15,0.5,oz,8,1,5,75,2,
special_with_carbs,food,350,200,grams,40,3,20,8,6,2.5
```

Notes:
- Empty `max_carbs` = calculate from other values
- Filled `max_carbs` = use direct value from label
- `max_moisture=0` = values already on dry matter basis
- `type=treat` = treats automatically limited to 10% of calories⁴

### Customizing Macronutrient Targets

Edit `config.py` to adjust target percentages:

```python
MACRONUTRIENT_TARGETS = {
    'protein': 55,  # Minimum protein percentage
    'carbs': 2,     # Maximum carbohydrate percentage
    'fat': 45       # Minimum fat percentage
}
```

These targets are based on the natural diet of wild cats: approximately 55% protein, 45% fat, and 1-2% carbohydrates.¹

## How It Works

### 1. Calorie Calculation (`calc_cal`)

Calculates daily calorie requirement per meal using the formula²:
```
resting_energy_requirement = (30 × weight_kg + 70) × activity_multiplier
Daily Calories = resting_energy_requirement × (0.8 if neutered, else 1.0)
Per Meal = Daily Calories / meal_count
```

**Activity Levels:**
- `1`: Low activity (1.2x multiplier) - Sedentary
- `2`: Medium activity (1.5x multiplier) - Moderately Active
- `3`: High activity (2.0x multiplier) - Highly Active

**Neutering Adjustment:** Neutered pets have a lower energy requirement, so multiply the TER by 0.8 for neutered cats.²

### 2. Optimization (`calc_quant`)

Uses a **two-stage optimization approach** for maximum efficiency and reliability:

**Stage 1: Standard Optimization**
- Uses linear programming to find optimal quantities without treat constraints
- Minimizes total quantity while meeting macronutrient targets
- Falls back to nonlinear optimization if linear programming fails

**Stage 2: Treat Inclusion (if requested)**
- Checks if Stage 1 already includes treats
- If not, uses **greedy substitution strategy**:
  - Tries substituting small amounts of food with treats
  - Maintains calorie balance and reasonable nutrition
  - Falls back to simple treat addition if substitution fails
- Ensures treats are limited to 10% of total calories

**Key Benefits:**
- **More reliable**: Avoids infeasible constraint combinations
- **Faster**: Two-stage approach is more efficient than complex single-stage optimization
- **Flexible**: Gracefully handles treat inclusion requests
- **Robust**: Multiple fallback strategies ensure solutions are found

### 3. Carbohydrate Calculation

Carbs are calculated from the guaranteed analysis using the formula from PetMD:³
```python
carbs = 100 - (protein + fat + fiber + moisture + ash)
```

This is necessary because AAFCO regulations don't require carb reporting on labels.

**Important Note:**³ Using crude fiber instead of total dietary fiber overestimates calculated carbs by approximately 21% on average (range: 3% to 93%). The optimizer accounts for this by adjusting calculated carb values downward when comparing to targets:
```python
adjusted_carbs = calculated_carbs * (1 - 0.21)
```

This ensures the optimization doesn't reject foods that actually meet carb targets but appear high due to the overestimation.

### 4. Treat Management

The optimizer distinguishes between food and treats to ensure proper nutrition:

- **Food**: Complete and balanced nutrition sources that can make up 90%+ of daily calories
- **Treats**: Limited to 10% of daily calories per [VCA Animal Hospitals](https://vcahospitals.com/know-your-pet/cat-treats)⁴

This constraint ensures that treats don't interfere with your cat's appetite for regular food or contribute to obesity, while still allowing for enrichment and bonding opportunities.

### 5. Dry Matter Basis Conversion

All foods are converted to dry matter basis for fair comparison, following TheCatSite methodology:⁴
```python
dry_mass = 100 - moisture_percent
adjusted_macro = (as_fed_macro / dry_mass) × 100
```

**Special case:** If moisture = 0, values are assumed to already be on dry matter basis (no conversion applied).

This ensures wet foods (78% moisture) and dry foods (8% moisture) are compared fairly.

## Module Documentation

### config.py
Configuration constants including:
- Weight conversion factors
- Macronutrient targets
- Carb overestimation factor (accounts for crude fiber overestimation)³

### nutrition.py
Core functionality:
- **Item class**: Represents a food item with nutritional data
  - Attributes: `name`, `calories_per_oz`, `min_protein`, `max_carbs`, `min_fat`
  - All nutrients automatically converted to dry matter basis for fair comparison
- **calc_cal()**: Calculate calorie requirements based on weight, activity, and meal count
- **calc_quant()**: Find optimal quantities using two-stage optimization approach
- **Item.__init__()**: Automatically converts all weights to ounces and nutrients to dry matter basis

### main.py
I/O operations:
- **load_items_from_csv()**: Reads CSV and creates Item objects
- **load_cat_config()**: Reads cat configuration from CSV
- **main()**: Application entry point

## Requirements

- Python 3.7+
- numpy >= 1.20.0
- scipy >= 1.7.0

## References

1. [The Complete Guide to Feline Nutrition](https://cats.com/the-complete-guide-to-feline-nutrition). Cats.com. Retrieved 2024.

2. [Metabolic Food Requirements for Your Pet](https://wilsonvet.net/metabolic-food-requirements-for-your-pet/). Wilson Veterinary Hospital. Retrieved 2024.

3. [Figuring Out Carb Levels in Cat Foods](https://www.petmd.com/blogs/nutritionnuggets/cat/dr-coates/2014/july/figuring-out-carb-levels-cat-foods-31869). PetMD. Published July 11, 2014.

4. [Cat Treats](https://vcahospitals.com/know-your-pet/cat-treats). VCA Animal Hospitals. Retrieved 2024.

5. [How to Compare Cat Foods - Calculate Carbs and Dry Matter Basis](https://thecatsite.com/c/how-to-compare-cat-foods-calculate-carbs-dry-matter-basis/). TheCatSite. Retrieved 2024.

## Contributing

Feel free to submit issues or pull requests for improvements.

## License

This project is open source and available for personal use.

