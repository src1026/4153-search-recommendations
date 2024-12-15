from pydantic import BaseModel
from typing import List, Optional

class SearchQuery(BaseModel):
    user_id: int
    keywords: List[str]
    ingredients: Optional[List[str]]

class Recommendation(BaseModel):
    user_id: int
    recommended_recipes: List[int]

#new classes for composite service
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

class RecipeSection(BaseModel):
    recipe_id: int
    recipe_name: str
    content: str
    create_time: Optional[str]
    likes: Optional[int] = 0

class RecipeCollection(BaseModel):
    name: str
    recipe_ids: List[int]

class UserCollection(BaseModel):
    name: str
    recipe_ids: List[int]