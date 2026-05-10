from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

import os
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/everyplate_db")
Base = declarative_base()
engine = create_engine(DB_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String, primary_key=True)  # Using EveryPlate's ID
    name = Column(String, nullable=False)
    headline = Column(String)
    rating = Column(Float)
    description = Column(Text)
    prep_time_minutes = Column(Integer)
    image_url = Column(String)
    pdf_link = Column(String)
    web_link = Column(String)

    # The JSONB Superpowers
    nutrition = Column(JSONB, default=dict)  # Dumps calories, fat, protein here
    allergens = Column(JSONB, default=list)  # Dumps ['Dairy', 'Nuts'] here
    instructions = Column(JSONB, default=list)  # Dumps the step-by-step array here

    # ORM Relationships (makes fetching linked data trivial)
    ingredients = relationship("RecipeIngredient", back_populates="recipe")
    tags = relationship("RecipeTag", back_populates="recipe")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)
    image_url = Column(String)

    recipes = relationship("RecipeIngredient", back_populates="ingredient")


class RecipeIngredient(Base):
    """The Join Table for your Grocery List engine"""

    __tablename__ = "recipe_ingredients"

    recipe_id = Column(String, ForeignKey("recipes.id"), primary_key=True)
    ingredient_id = Column(String, ForeignKey("ingredients.id"), primary_key=True)

    amount = Column(Float)
    unit = Column(String)

    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipes")


class Tag(Base):
    """For categories like 'Vegetarian', 'Fast', 'Spicy'"""

    __tablename__ = "tags"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)


class RecipeTag(Base):
    __tablename__ = "recipe_tags"

    recipe_id = Column(String, ForeignKey("recipes.id"), primary_key=True)
    tag_id = Column(String, ForeignKey("tags.id"), primary_key=True)

    recipe = relationship("Recipe", back_populates="tags")
