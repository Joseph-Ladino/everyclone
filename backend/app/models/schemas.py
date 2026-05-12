from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import re

# Compile outside the function so Python only builds the state machine once
HOUR_PATTERN = re.compile(r"(\d+)H")
MIN_PATTERN = re.compile(r"(\d+)M")

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
        """Extracts total minutes from an ISO 8601 duration string like 'PT1H30M'"""
        if not v:
            return 0
            
        h_match = HOUR_PATTERN.search(v)
        m_match = MIN_PATTERN.search(v)
        
        hours = int(h_match.group(1)) * 60 if h_match else 0
        minutes = int(m_match.group(1)) if m_match else 0
        
        return hours + minutes