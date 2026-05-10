import json
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, Recipe, Ingredient, RecipeIngredient, Tag, RecipeTag
from models.schemas import EPRecipe

# Boot up the Database Connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/everyplate_db")
engine = create_engine(DB_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def clean_title(text: str | None) -> str:
    """Strips out the '| 2-4 Servings' and '| Serves 2-3' bloat from strings."""
    if not text:
        return ""
    return re.sub(r"\s*\|.*(?:[Ss]erving|[Ss]erves).*", "", text).strip()


def run_ingestion():
    db = SessionLocal()

    # --- IN-MEMORY CACHE ---
    seen_tags = {t[0] for t in db.query(Tag.id).all()}
    seen_ingredients = {i[0] for i in db.query(Ingredient.id).all()}
    seen_recipe_names = {r[0] for r in db.query(Recipe.name).all()}
    
    # Track the ghosts we've already compensated for
    promoted_ghosts = set()

    print("Loading JSON dump into memory... give it a second.")
    with open("data/everyplate_dump_2.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # --- THE PRE-FLIGHT SCAN ---
    all_dump_ids = {item.get("id") for item in raw_data if item.get("id")}

    print(f"Found {len(raw_data)} raw recipes. Firing up the pipeline...")

    for item in raw_data:
        try:
            clean_data = EPRecipe(**item)
        except Exception:
            continue  

        # --- THE HIGHLANDER CLONE KILLER ---
        if clean_data.clonedFrom:
            if clean_data.clonedFrom in all_dump_ids:
                # The original base recipe is in this file. Safe to drop the clone.
                continue
            else:
                # The base is a ghost. 
                if clean_data.clonedFrom in promoted_ghosts:
                    # We already promoted a different clone for this ghost. Kill this one.
                    continue
                else:
                    # This is the first clone we've seen for this ghost. Keep it and log it.
                    promoted_ghosts.add(clean_data.clonedFrom)

        # Verify it has a 2-serving option BEFORE we touch the database
        yield_2 = next((y for y in clean_data.yields if y.yields == 2), None)
        if not yield_2:
            continue

        final_name = clean_title(clean_data.name)
        final_headline = clean_title(clean_data.headline)

        if final_name in seen_recipe_names:
            continue

        # --- THE FIX: DEDUPLICATE THE ARRAYS BEFORE LOOPING ---
        # This neutralizes EveryPlate's garbage duplicate data automatically.
        unique_tags = {t.id: t for t in clean_data.tags}.values()
        unique_ingredients = {i.id: i for i in clean_data.ingredients}.values()

        # --- TRACKERS FOR CACHE REVERTING ---
        new_tags_this_loop = set()
        new_ingredients_this_loop = set()

        image_url = None
        if clean_data.imagePath:
            image_url = "https://media.everyplate.com/w_1080,q_auto,f_auto,c_limit,fl_lossy/everyplate_s3" + clean_data.imagePath

        db_recipe = Recipe(
            id=clean_data.id,
            name=final_name,
            headline=final_headline,
            rating=clean_data.averageRating,
            description=clean_data.description,
            prep_time_minutes=clean_data.prepTime,
            image_url= image_url,
            pdf_link=clean_data.cardLink,
            web_link=clean_data.websiteUrl,
            nutrition=clean_data.nutrition,
            allergens=[a.name for a in clean_data.allergens],
            instructions=clean_data.steps,
        )
        db.add(db_recipe)
        seen_recipe_names.add(final_name)

        for tag_data in unique_tags:
            if tag_data.id not in seen_tags:
                db.add(Tag(id=tag_data.id, name=tag_data.name))
                seen_tags.add(tag_data.id)
                new_tags_this_loop.add(tag_data.id)  # Track it

        for ing in unique_ingredients:
            if ing.id not in seen_ingredients:
                ingredient_image_url = None
                if ing.imagePath:
                    ingredient_image_url = "https://media.everyplate.com/w_1080,q_auto,f_auto,c_limit,fl_lossy/everyplate_s3" + ing.imagePath
                db.add(
                    Ingredient(
                        id=ing.id,
                        name=ing.name,
                        category=ing.family.name if ing.family else "Other",
                        image_url=ingredient_image_url,
                    )
                )
                seen_ingredients.add(ing.id)
                new_ingredients_this_loop.add(ing.id)  # Track it

        db.flush()

        for tag_data in unique_tags:
            db.add(RecipeTag(recipe_id=db_recipe.id, tag_id=tag_data.id))

        yield_dict = {yi.id: yi for yi in yield_2.ingredients}
        for ing in unique_ingredients:
            amount_info = yield_dict.get(ing.id)
            if amount_info:
                db.add(
                    RecipeIngredient(
                        recipe_id=db_recipe.id,
                        ingredient_id=ing.id,
                        amount=amount_info.amount,
                        unit=amount_info.unit,
                    )
                )

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            # --- THE SAFETY NET: REVERT THE PYTHON CACHE ---
            seen_tags -= new_tags_this_loop
            seen_ingredients -= new_ingredients_this_loop
            seen_recipe_names.discard(final_name)

            print(f"Failed to insert recipe {clean_data.id}: {e}")

    print("Ingestion complete. Database is seeded.")


if __name__ == "__main__":
    run_ingestion()
