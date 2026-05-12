import json
from sqlalchemy.orm import Session
from models.database import SessionLocal, Ingredient

def run_backfill():
    db = SessionLocal()

    print("Loading local JSON data...")
    try:
        with open("./data/everyplate_spice_recipes.json", "r", encoding="utf-8") as f:
            spices_data = json.load(f)
            
        with open("./data/everyplate_unit_conversions.json", "r", encoding="utf-8") as f:
            units_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Could not find JSON files. {e}")
        return

    # 1. Backfill Unit Conversions (Apply to ALL duplicates)
    print("Backfilling unit conversions...")
    for name, data in units_data.items():
        db_ings = db.query(Ingredient).filter(Ingredient.name.ilike(f"%{name}%")).all()
        for db_ing in db_ings:
            db_ing.unit_conversion = { "amount": data["amount"], "unit": data["unit"] } #type: ignore 

    # 2. Backfill Spice Blends (Apply to ALL duplicates)
    print("Backfilling proprietary spice blends...")
    for name, spice in spices_data.items():
        raw_spice_name = name
        
        # The Fix: Strip common suffixes to cast a wider net
        search_term = raw_spice_name.replace(" Blend", "").strip()
        
        # Now searching for "%Italian Seasoning%" instead of "%Italian Seasoning Blend%"
        db_ings = db.query(Ingredient).filter(Ingredient.name.ilike(f"%{search_term}%")).all()
        for db_ing in db_ings:
            db_ing.is_blend = True #type: ignore
            db_ing.blend_recipe = spice #type: ignore
            db_ing.unit_conversion = { "amount": 1, "unit": "tbsp" } #type: ignore

    db.commit()
    print("Database backfill complete! Your ingredients are now fully enriched.")

if __name__ == "__main__":
    run_backfill()