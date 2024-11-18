from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.models.search_rec import UserPreference, RecipeFeedback, SearchHistory
import httpx

router = APIRouter()

# Interacting with Recipe Management Service

# Helper Functions
async def fetch_paginated_recipes(skip: int = 0, limit: int = 10, filter_by: Optional[str] = None):
    """Fetch recipes with pagination from the recipe management service."""
    params = {"offset": skip, "limit": limit, "filter_by": filter_by}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RECIPE_MANAGEMENT_BASE_URL}/recipes_sections", params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch recipes")
        recipes = response.json()
        return [RecipeSection(**recipe) for recipe in recipes]  # Validate with RecipeSection model

async def fetch_recipe_by_id(recipe_id: str):
    """Fetch a specific recipe by ID."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RECIPE_MANAGEMENT_BASE_URL}/recipes_sections/{recipe_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Recipe not found")
        return RecipeSection(**response.json())  # Validate with RecipeSection model

@routers.get("/recipes/suggestions", response_model=List[RecipeSection])
async def get_aggregated_suggestions(
    cuisine: Optional[str] = None,
    dietary_preference: Optional[str] = None,
    sort_by: str = Query("popularity", enum=["popularity", "recency"]),
    skip: int = 0,
    limit: int = 10,
):
    #Get: Filters by cuisine and diet, sort by popularity and most recent, support pagination with skip and limit
    
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
    # add functionality for updating database
    return {"message": "Preferences updated successfully", "data": preferences.dict()}

@routers.post("/recipes/comment", status_code=201)
async def submit_recipe_feedback(feedback: RecipeComment):
    # user provides comment -> update database
        async with httpx.AsyncClient() as client:
        # Construct the payload for the recipe management service
        payload = feedback.dict()
        
        # Send the feedback to the recipe management service
        response = await client.put(
            f"{RECIPE_MANAGEMENT_BASE_URL}/recipes_sections/{feedback.recipe_id}/feedback",
            json=payload
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to update feedback in recipe management: {response.text}"
            )
    return {"message": "Comment submitted successfully", "data": comment.dict()}
