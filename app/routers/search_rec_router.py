from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.models.composite_models import UserPreference, RecipeFeedback, SearchHistory
from app.resources.recipe_resource import RecipeResource

router = APIRouter()

# Dependency injection
def get_recipe_resource() -> RecipeResource:
    return RecipeResource(base_url="http://recipe-management-service")

@routers.get("/recipes/suggestions")
async def get_aggregated_suggestions(
    cuisine: Optional[str] = None,
    dietary_preference: Optional[str] = None,
    sort_by: str = Query("popularity", enum=["popularity", "recency"]),
    recipe_resource: RecipeResource = Depends(get_recipe_resource),
):
    recipes = recipe_resource.get_paginated_recipes(filter_by=cuisine, limit=100)
    if dietary_preference:
        recipes = [r for r in recipes if dietary_preference.lower() in r["content"].lower()]
    if sort_by == "popularity":
        recipes = sorted(recipes, key=lambda r: (-r["rating"], r["recipe_name"]))
    elif sort_by == "recency":
        recipes = sorted(recipes, key=lambda r: r["create_time"], reverse=True)
    return recipes[:10]

@routers.put("/preferences")
async def update_user_preferences(preferences: UserPreference):
    # Logic to handle preferences can be added here
    return {"message": "Preferences updated successfully", "data": preferences.dict()}

@routers.post("/recipes/feedback")
async def submit_recipe_feedback(feedback: RecipeFeedback):
    # Logic to log feedback
    return {"message": "Feedback submitted successfully", "data": feedback.dict()}
