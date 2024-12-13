from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.models.search_rec import UserPreference, RecipeFeedback, SearchHistory, RecipeComment, RecipeCollection
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
        data = response.json()
        recipes = [RecipeSection(**recipe) for recipe in data["data"]]
        total_count = data["pagination"]["total_count"]
        return recipes, total_count

async def fetch_recipe_by_id(recipe_id: str):
    """Fetch a specific recipe by ID."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RECIPE_MANAGEMENT_BASE_URL}/recipes_sections/{recipe_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Recipe not found")
        return RecipeSection(**response.json())  # Validate with RecipeSection model

async def get_like_counts(recipe_ids: List[int]):
    """Fetch like counts from the User Interaction Microservice."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_INTERACTION_BASE_URL}/likes",
            json={"recipe_ids": recipe_ids},
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch like counts")
        return response.json()

@router.get("/recipes/suggestions", response_model=List[RecipeSection])
async def get_aggregated_suggestions(
    cuisine: Optional[str] = None,
    dietary_preference: Optional[str] = None,
    sort_by: str = Query("popularity", enum=["popularity", "recency"]),
    skip: int = 0,
    limit: int = 10,
):
    # Fetch recipes from Recipe Management Microservice
    recipes, _ = await fetch_paginated_recipes(skip=skip, limit=100, filter_by=cuisine)

    # Fetch like counts from User Interaction Microservice
    recipe_ids = [r.recipe_id for r in recipes]
    like_counts = await get_like_counts(recipe_ids)

    # Add like counts to recipes
    for recipe in recipes:
        recipe.likes = like_counts.get(recipe.recipe_id, 0)

    if dietary_preference:
        recipes = [r for r in recipes if dietary_preference.lower() in r.content.lower()]
    if sort_by == "popularity":
        recipes = sorted(recipes, key=lambda r: (-r.rating, r.recipe_name))
    elif sort_by == "recency":
        recipes = sorted(recipes, key=lambda r: r.create_time, reverse=True)
    return recipes[:limit]
'''
@router.put("/preferences")
async def update_user_preferences(user_id: int, preferences: UserPreference):
    """Update user preferences."""
    success = await user_interaction_resource.update_user_preferences(user_id, preferences.dict())
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update preferences")
    return {"message": "Preferences updated successfully"}
'''
@router.post("/recipes/comment", status_code=201)
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
    return {"message": "Comment submitted successfully", "data": feedback.dict()}

@router.post("/collections", status_code=201)
async def create_recipe_collection(user_id: int, collection: RecipeCollection):
    """Create a user-generated recipe collection/favorites."""
    success = await user_interaction_resource.create_collection(user_id, collection.dict())
    if not success:
        raise HTTPException(status_code=400, detail="Failed to create collection")
    return {"message": "Collection created successfully"}

