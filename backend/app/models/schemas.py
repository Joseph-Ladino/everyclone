from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import re


# --- INGREDIENT SCHEMAS ---
class EPIngredientFamily(BaseModel):
    name: str


class EPIngredient(BaseModel):
    id: str
    name: str
    imagePath: Optional[str] = None
    family: Optional[EPIngredientFamily] = None


# --- YIELD SCHEMAS (For the Join Table) ---
class EPYieldIngredient(BaseModel):
    id: str
    amount: Optional[float] = 0.0  # Catches the 'null' salt/pepper issue
    unit: Optional[str] = ""


class EPYield(BaseModel):
    yields: int
    ingredients: List[EPYieldIngredient]


# --- TAG SCHEMAS ---
class EPTag(BaseModel):
    id: str
    name: str


# --- ALLERGEN & NUTRITION SCHEMAS ---
class EPAllergen(BaseModel):
    name: str


# --- THE MAIN RECIPE SCHEMA ---
class EPRecipe(BaseModel):
    id: str
    name: str
    prepTime: str
    headline: Optional[str] = ""
    averageRating: Optional[float] = 0.0
    description: Optional[str] = ""
    imagePath: Optional[str] = None
    cardLink: Optional[str] = None
    websiteUrl: Optional[str] = None
    clonedFrom: Optional[str] = None

    ingredients: List[EPIngredient]
    yields: List[EPYield]
    tags: List[EPTag]

    # We leave these as un-validated lists of dicts for the JSONB columns
    nutrition: List[Dict[str, Any]] = []
    allergens: List[EPAllergen] = []
    steps: List[Dict[str, Any]] = []

    @field_validator("prepTime")
    @classmethod
    def parse_prep_time(cls, v: str) -> int:
        """Extracts the integer from an ISO 8601 string like 'PT25M'"""
        if not v:
            return 0
        match = re.search(r"PT(\d+)M", v)
        return int(match.group(1)) if match else 0
