from pydantic import BaseModel
from typing import List, Optional

class SearchQuery(BaseModel):
    user_id: int
    keywords: List[str]
    ingredients: Optional[List[str]]

class Recommendation(BaseModel):
    user_id: int
    recommended_recipes: List[int]
