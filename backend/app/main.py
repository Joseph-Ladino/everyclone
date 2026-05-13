from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
from pydantic import BaseModel
from collections import Counter, defaultdict
import random
import math
import os

from app.models.database import SessionLocal, Recipe, Ingredient, RecipeIngredient, Tag, RecipeTag

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
origins = [FRONTEND_URL, "http://localhost:8081"]

app = FastAPI(title="EveryPlate Proxy Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_grocery_aisle(ingredient_name: str) -> str:
    """A prioritized lexical scanner to sort ingredients into supermarket aisles."""
    name = ingredient_name.lower()

    # Order matters. We check these buckets sequentially.
    taxonomy = {
        # Spices MUST go first to catch "Garlic Powder" or "Dried Parsley"
        # before the Produce bucket catches the raw root words.
        "Spices & Seasonings": [
            "salt",
            "black pepper",
            "white pepper",
            "paprika",
            "garlic powder",
            "onion powder",
            "spice",
            "seasoning",
            "powder",
            "blend",
            "rub",
            "flakes",
            "dried",
            "cumin",
            "cayenne",
            "coriander",
            "oregano",
            "thyme",
            "basil",
            "cinnamon",
            "clove",
            "allspice",
            "nutmeg",
            "turmeric",
            "sumac",
        ],
        "Pantry & Dry Goods": [
            "rice",
            "pasta",
            "couscous",
            "spaghetti",
            "penne",
            "macaroni",
            "flour",
            "sugar",
            "oil",
            "almond",
            "peanut",
            "walnut",
            "sesame",
            "seed",
            "panko",
            "breadcrumbs",
        ],
        "Sauces & Condiments": [
            "soy sauce",
            "pesto",
            "mayo",
            "ketchup",
            "mustard",
            "vinegar",
            "hot sauce",
            "sriracha",
            "paste",
            "concentrate",
            "stock",
            "broth",
            "jam",
            "glaze",
            "dressing",
            "sauce",
            "syrup",
            "honey",
        ],
        "Seafood": [
            "shrimp",
            "salmon",
            "tilapia",
            "barramundi",
            "cod",
            "trout",
            "fish",
        ],
        "Dairy & Eggs": [
            "cheese",
            "milk",
            "butter",
            "egg",
            "sour cream",
            "yogurt",
            "crema",
            "parmesan",
            "gouda",
            "cheddar",
            "mozzarella",
            "jack",
        ],
        "Bakery": [
            "bun",
            "bread",
            "tortilla",
            "flatbread",
            "baguette",
            "pita",
            "crust",
            "roll",
        ],
        "Produce": [
            "onion",
            "garlic",
            "chives",
            "lemon",
            "lime",
            "potato",
            "carrot",
            "scallion",
            "tomato",
            "pepper",
            "ginger",
            "zucchini",
            "broccoli",
            "lettuce",
            "cabbage",
            "cilantro",
            "parsley",
            "dill",
            "apple",
            "cucumber",
            "arugula",
            "spinach",
            "mushroom",
            "celery",
            "shallot",
        ],
        "Meat & Poultry": [
            "chicken",
            "beef",
            "pork",
            "sausage",
            "turkey",
            "bacon",
            "steak",
            "prosciutto",
            "chorizo",
            "meatball",
        ],
    }

    for aisle, keywords in taxonomy.items():
        if any(word in name for word in keywords):
            return aisle

    return "Misc / Other"


def normalize_volume(amount, unit):
    """Converts standard cooking volumes to teaspoons."""
    if not amount or not unit:
        return amount, unit, False

    u = unit.lower()
    if "cup" in u or "(c)" in u:
        return amount * 48.0, "tsp", True
    if "tablespoon" in u or "tbsp" in u:
        return amount * 3.0, "tsp", True
    if "teaspoon" in u or "tsp" in u:
        return amount, "tsp", True

    return amount, unit, False


def optimize_volume(amount, unit):
    """Scales teaspoons back up to the highest clean unit."""
    if unit == "tsp":
        if amount >= 48:
            return amount / 48.0, "cup"
        if amount >= 3:
            return amount / 3.0, "tbsp"
    return amount, unit


# --- Pydantic Models ---
class RecipeOut(BaseModel):
    id: str
    name: str
    headline: str | None
    rating: float | None
    prep_time_minutes: int
    image_url: str | None

    class Config:
        from_attributes = True

class RecipePageOut(BaseModel):
    total: int
    skipped: int
    recipes: List[RecipeOut]

class GroceryListRequest(BaseModel):
    recipe_scales: dict[str, float] # e.g., {"recipe_id_1": 1.0, "recipe_id_2": 1.5}

class MenuProposalRequest(BaseModel):
    target_meals: int = 5
    history_ids: List[str] = []  
    min_rating: float = 3.5      
    # Allow the frontend to pass specific anchors (like what's already in the freezer)
    # If empty, the backend will pick them randomly.
    target_anchors: List[str] = []

@app.get("/api/recipes/{recipe_id}")
def get_full_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Dumps every single piece of data we have on a specific recipe."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Manually join and format the ingredients
    links = db.query(RecipeIngredient, Ingredient).join(Ingredient).filter(
        RecipeIngredient.recipe_id == recipe_id
    ).all()

    ingredients_data = [
        {
            "id": ing.id,
            "name": ing.name,
            "category": ing.category,
            "image_url": ing.image_url,
            "amount": link.amount,
            "unit": link.unit,
            "is_blend": ing.is_blend,
            "unit_conversion": ing.unit_conversion,
        }
        for link, ing in links
    ]

    # Manually join the tags
    tag_links = db.query(RecipeTag, Tag).join(Tag).filter(
        RecipeTag.recipe_id == recipe_id
    ).all()

    return {
        "id": recipe.id,
        "name": recipe.name,
        "headline": recipe.headline,
        "rating": recipe.rating,
        "description": recipe.description,
        "prep_time_minutes": recipe.prep_time_minutes,
        "image_url": recipe.image_url,
        "pdf_link": recipe.pdf_link,
        "web_link": recipe.web_link,
        "nutrition": recipe.nutrition,
        "allergens": recipe.allergens,
        "instructions": recipe.instructions,
        "ingredients": ingredients_data,
        "tags": [tag.name for link, tag in tag_links]
    }

@app.get("/api/ingredients/{ingredient_id}")
def get_full_ingredient(ingredient_id: str, db: Session = Depends(get_db)):
    """Dumps ingredient data and calculates how many recipes use it."""
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    # Calculate usage frequency for stats
    usage_count = db.query(RecipeIngredient).filter(
        RecipeIngredient.ingredient_id == ingredient_id
    ).count()

    return {
        "id": ing.id,
        "name": ing.name,
        "category": ing.category,
        "image_url": ing.image_url,
        "is_blend": ing.is_blend,
        "blend_recipe": ing.blend_recipe,
        "unit_conversion": ing.unit_conversion,
        "used_in_recipes_count": usage_count
    }

@app.get("/api/recipes", response_model=RecipePageOut)
def get_recipes(limit: int = 5, skip: int = 0, db: Session = Depends(get_db)):
    """Fetches a paginated list of all meals for the UI to display."""

    allRecipes = db.query(Recipe)
    total = allRecipes.count()
    recipes = allRecipes.offset(skip).limit(limit).all()
    skipped = min(total, skip + limit)

    return {
        "total": total,
        "skipped": skipped,
        "recipes": recipes
    }

@app.get("/api/random/recipes", response_model=List[str])
def get_random_recipe_ids(limit: int = 5, db: Session = Depends(get_db)):
    """Fetches a paginated list of all meals for the UI to display."""
    ids = db.query(Recipe.id).order_by(func.random()).limit(limit).all()
    return [id[0] for id in ids]

@app.post("/api/grocery-list")
def generate_grocery_list(request: GroceryListRequest, db: Session = Depends(get_db)):
    """The Categorized Bulk-Optimized Grocery Engine."""

    unique_recipe_ids = list(request.recipe_scales.keys())

    items = db.query(RecipeIngredient, Ingredient).join(Ingredient).filter(
        RecipeIngredient.recipe_id.in_(unique_recipe_ids)
    ).all()

    if not items:
        raise HTTPException(status_code=404, detail="No ingredients found for these recipes.")

    # ONE dictionary to rule them all
    grocery_dict = defaultdict(dict)

    for link, ingredient in items:
        name_lower = ingredient.name.strip().lower()
        category = get_grocery_aisle(ingredient.name)

        if name_lower not in grocery_dict[category]:
            grocery_dict[category][name_lower] = {
                "name": ingredient.name,
                "amount": 0.0,
                "unit": link.unit or "",
                "unit_conversion": ingredient.unit_conversion
            }

        if link.amount:
            multiplier = request.recipe_scales.get(link.recipe_id, 1.0)
            added_amount = link.amount * multiplier

            add_amt_norm, add_unit_norm, is_vol = normalize_volume(
                added_amount, link.unit or ""
            )

            curr_amt = grocery_dict[category][name_lower]["amount"]
            curr_unit = grocery_dict[category][name_lower]["unit"]
            curr_amt_norm, _, curr_is_vol = normalize_volume(curr_amt, curr_unit)

            if is_vol or curr_is_vol:
                grocery_dict[category][name_lower]["amount"] = (
                    curr_amt_norm + add_amt_norm
                )
                grocery_dict[category][name_lower][
                    "unit"
                ] = "tsp"  # Temporary holding unit
            else:
                grocery_dict[category][name_lower]["amount"] += added_amount

    # optimize volume for "duplicate" ingredients
    for cat in grocery_dict:
        for name_lower in grocery_dict[cat]:
            item = grocery_dict[cat][name_lower]
            opt_amt, opt_unit = optimize_volume(item["amount"], item["unit"])
            item["amount"] = opt_amt
            item["unit"] = opt_unit

    # Sort the single dictionary
    formatted = {}
    for cat, items_dict in grocery_dict.items():
        formatted[cat] = sorted(list(items_dict.values()), key=lambda x: x["name"])

    return formatted

@app.post("/api/propose-menu")
def propose_menu(request: MenuProposalRequest, db: Session = Depends(get_db)):
    """
    The Bulk-Optimized Menu Generator.
    Uses a greedy overlap algorithm with an anchor cap to prevent runaway feedback loops.
    """

    standard_anchors = ["chicken", "beef", "pork", "sausage"]
    
    anchors = [a.lower() for a in request.target_anchors]
    if not anchors:
        anchors = random.sample(standard_anchors, 2)

    # Calculate the hard limit for any single protein
    max_per_anchor = math.ceil(request.target_meals / len(anchors))
    anchor_counts = {anchor: 0 for anchor in anchors}

    candidates = db.query(Recipe).options(
        joinedload(Recipe.ingredients)
    ).filter(
        ~Recipe.id.in_(request.history_ids),
        Recipe.rating >= request.min_rating
    ).limit(300).all() 

    valid_candidates: list[Recipe] = []
    for recipe in candidates:
        name_lower = recipe.name.lower()
        if any(anchor in name_lower for anchor in anchors):
            valid_candidates.append(recipe)

    if not valid_candidates:
        raise HTTPException(status_code=404, detail="Not enough meals found with those anchors.")

    # Initialize the Menu with a random Seed Meal
    final_menu = [random.choice(valid_candidates)]
    valid_candidates.remove(final_menu[0])
    current_ingredient_needs = {link.ingredient_id for link in final_menu[0].ingredients}

    # Track the seed meal's anchor
    for anchor in anchors:
        if anchor in final_menu[0].name.lower():
            anchor_counts[anchor] += 1
            break

    # The Capped Greedy Overlap Loop
    while len(final_menu) < request.target_meals and valid_candidates:
        best_recipe = None
        best_score = -1
        
        # THE HARD WALL: Filter out maxed-out anchors before we even look at scores
        available_candidates = []
        for recipe in valid_candidates:
            primary_anchor = next((a for a in anchors if a in recipe.name.lower()), None)
            if primary_anchor and anchor_counts[primary_anchor] >= max_per_anchor:
                continue
            available_candidates.append(recipe)
            
        # If we exhausted all options that fit our protein caps, bail out
        if not available_candidates:
            break
            
        for recipe in available_candidates:
            recipe_ing_ids = {link.ingredient_id for link in recipe.ingredients}
            overlap_score = len(current_ingredient_needs.intersection(recipe_ing_ids))
            
            # The penalty check
            if overlap_score > (len(recipe_ing_ids) * 0.8): 
                continue # Skip it entirely, don't even let it score
                
            if overlap_score > best_score:
                best_score = overlap_score
                best_recipe = recipe

        if best_recipe:
            final_menu.append(best_recipe)
            valid_candidates.remove(best_recipe)
            current_ingredient_needs.update({link.ingredient_id for link in best_recipe.ingredients})
            
            primary_anchor = next((a for a in anchors if a in best_recipe.name.lower()), None)
            if primary_anchor:
                anchor_counts[primary_anchor] += 1
        else:
            # If everything failed the 80% check, grab a random one from the 
            # available_candidates (which is already pre-filtered for the protein cap!)
            fallback = random.choice(available_candidates)
            final_menu.append(fallback)
            valid_candidates.remove(fallback)
            current_ingredient_needs.update({link.ingredient_id for link in fallback.ingredients})
            
            primary_anchor = next((a for a in anchors if a in fallback.name.lower()), None)
            if primary_anchor:
                anchor_counts[primary_anchor] += 1

    result = []
    for recipe in final_menu:
        # We manually bridge the gap between the link table and the ingredient table
        ingredients_data = [{
            "id": link.ingredient.id,
            "name": link.ingredient.name,
            "amount": link.amount,
            "unit": link.unit,
            "image_url": link.ingredient.image_url,
            "is_blend": link.ingredient.is_blend,
            "blend_recipe": link.ingredient.blend_recipe,
            "unit_conversion": link.ingredient.unit_conversion
        } for link in recipe.ingredients]

        result.append({
            "id": recipe.id,
            "name": recipe.name,
            "headline": recipe.headline,
            "rating": recipe.rating,
            "prep_time_minutes": recipe.prep_time_minutes,
            "image_url": recipe.image_url,
            "ingredients": ingredients_data,
            "calories": recipe.nutrition[0]["amount"]
        })

    return result
