from typing import List, Optional
from pydantic import BaseModel

class Link(BaseModel):
    rel: str
    href: str
    method: str

class RecipeSection(BaseModel):
    recipe_id: int
    recipe_name: Optional[str] = None
    user_id: Optional[int] = None
    content: Optional[str] = None
    rating: Optional[float] = None
    cuisine_id: Optional[int] = None
    ingredient_id: Optional[str] = None
    comment: Optional[str] = None
    cooking_time: Optional[int] = None
    create_time: Optional[str] = None
    pictures: Optional[str] = None
    links: Optional[List[Link]] = None
    likes: Optional[int] = 0  # Added locally if we want to store like counts

class SearchQuery(BaseModel):
    user_id: int
    keywords: List[str] = []
    ingredients: List[str] = []

class Recommendation(BaseModel):
    user_id: int
    recommended_recipes: List[int]

class UserPreferences(BaseModel):
    exclude_ingredients: Optional[List[str]] = None
    preferred_tags: Optional[List[str]] = None

class RecipeComment(BaseModel):
    recipe_id: int
    comment: str
    rating: Optional[float] = None

class SearchHistory(BaseModel):
    user_id: int
    query: str