"""
Configuration constants for the nutrition optimization module.
"""

# Weight conversion constants (all to ounces)
OZ_PER_LB = 16.0
GRAMS_PER_OZ = 28.3495
KG_TO_OZ = GRAMS_PER_OZ * 1000

# Conversion factors to ounces for different weight units
WEIGHT_CONVERSION = {
    'oz': 1.0,
    'ozs': 1.0,
    'ounce': 1.0,
    'ounces': 1.0,
    'lb': OZ_PER_LB,
    'lbs': OZ_PER_LB,
    'pound': OZ_PER_LB,
    'pounds': OZ_PER_LB,
    'g': 1.0 / GRAMS_PER_OZ,
    'gram': 1.0 / GRAMS_PER_OZ,
    'grams': 1.0 / GRAMS_PER_OZ,
    'kg': KG_TO_OZ,
    'kilogram': KG_TO_OZ,
    'kilograms': KG_TO_OZ,
    'kilo': KG_TO_OZ,
}

# Macronutrient targets (percentages)
MACRONUTRIENT_TARGETS = {
    'protein': 55,  # Minimum protein percentage
    'carbs': 2,     # Maximum carbohydrate percentage
    'fat': 45       # Minimum fat percentage
}

# Treat inclusion preference
# When True, ensures at least one treat is included in the meal
# When False, optimizes purely for nutrition (treats optional)
INCLUDE_TREAT_BY_DEFAULT = False

# Carb overestimation factor (per PetMD source³)
# Using crude fiber instead of total dietary fiber overestimates carbs by ~21%
# We apply this factor to adjust calculated carb values downward
CARB_OVERESTIMATION_FACTOR = 0.21

