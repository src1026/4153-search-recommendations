from fastapi import APIRouter, Query, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from app.models.search_rec import UserPreferences, SearchHistory, RecipeComment
from app.models.search_rec import RecipeSection, UserCollection, RecipeCollection
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

@router.get("/recipes/suggestions", 
            response_model=List[RecipeSection],
            tags=["Recipes"],
            status_code=status.HTTP_200_OK,
            summary="Get recipe suggestions",
            description="Retrieve suggestions based on cuisine, dietary preference, and sort by popularity.",
            responses={
        200: {
            "description": "Successfully retrieved recipe suggestions",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "recipe_id": 1,
                            "recipe_name": "Pasta",
                            "content": "Boil pasta, cook sauce, mix ingredients.",
                            "cuisine_id": 2,
                            "likes": 42,
                            "create_time": "2024-01-01T12:00:00"
                        }
                    ]
                }
            }
        },
        400: {"description": "Invalid input data"},
        500: {"description": "Failed to fetch recipes"}
    }
)
async def get_aggregated_suggestions(
    cuisine: Optional[str] = None,
    dietary_preference: Optional[str] = None,
    sort_by: str = Query("popularity", enum=["popularity", "recency"]),
    skip: int = 0,
    limit: int = 10,
):
    recipes, _ = await fetch_paginated_recipes(skip=skip, limit=100, filter_by=cuisine)

    recipe_ids = [r.recipe_id for r in recipes]
    like_counts = await get_like_counts(recipe_ids)

    for recipe in recipes:
        recipe.likes = like_counts.get(recipe.recipe_id, 0)

    if dietary_preference:
        recipes = [r for r in recipes if dietary_preference.lower() in r.content.lower()]

    if sort_by == "popularity":
        recipes = sorted(recipes, key=lambda r: (-r.likes, r.recipe_name))
    elif sort_by == "recency":
        recipes = sorted(recipes, key=lambda r: r.create_time, reverse=True)

    return recipes[:limit]

@router.put("/preferences",
            tags=["User Preferences"],
            status_code=status.HTTP_200_OK,
            summary="Update user preferences",
            description="Update user preferences such as cuisine or dietary restrictions.",
            responses={
                200: {"description": "Preferences updated successfully"},
                400: {"description": "Failed to update preferences"}
            }
)
async def update_user_preferences(user_id: int, preferences: UserPreferences):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{USER_INTERACTION_BASE_URL}/preferences/{user_id}", json=preferences.dict())
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to update preferences")
    return {"message": "Preferences updated successfully"}


@router.post("/recipes/comment", 
             tags=["Recipes"],
             status_code=status.HTTP_201_CREATED,
             summary="Submit recipe feedback",
             description="Add feedback or a comment for a recipe.",
             responses={
                 201: {"description": "Comment submitted successfully"},
                 500: {"description": "Failed to submit feedback"}
             }
)
async def submit_recipe_feedback(feedback: RecipeComment):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{RECIPE_MANAGEMENT_BASE_URL}/recipes_sections/{feedback.recipe_id}/feedback",
            json=feedback.dict()
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to submit feedback")
    return {"message": "Comment submitted successfully"}

@router.post("/collections", 
             status_code=status.HTTP_201_CREATED,
             summary="Create a collection",
             description="Create a collection of recipes under the user account with unique user ID.",
             responses={
                 201: {"description": "Collection created successfully"},
                 500: {"description": "Failed to create collection"}
             }
             )
async def create_recipe_collection(user_id: int, collection: UserCollection):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_INTERACTION_BASE_URL}/collections/{user_id}", json=collection.dict())
        if response.status_code != 201:
            raise HTTPException(status_code=400, detail="Failed to create collection")
    return {"message": "Collection created successfully"}

@router.get("/recipes/explore", 
            response_model=List[RecipeSection],
            tags=["Recipes"],
            summary="Explore recipes",
            description="Discover recipes by category.",
            responses={
                200: {
                    "description": "Successfully fetched explore recipes",
                    "content": {
                        "application/json": {
                            "example": [
                                {
                                    "recipe_id": 1,
                                    "recipe_name": "Pasta",
                                    "content": "Boil pasta, cook sauce, mix ingredients.",
                                    "likes": 42,
                                    "create_time": "2023-12-01T09:00:00"
                                }
                            ]
                        }
                    }
                },
                500: {"description": "Failed to fetch explore recipes"}
            })
async def explore_recipes(category: Optional[str] = None):
    async with httpx.AsyncClient() as client:
        params = {"category": category}
        response = await client.get(f"{RECIPE_MANAGEMENT_BASE_URL}/explore", params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch explore recipes")
    return response.json()

@router.put("/recipes/feedback",
            tags=["Recipes"],
            status_code=status.HTTP_201_CREATED,
            summary="Submit comment to recipe",
            description="Add a comment under a recipe.",
            responses={
                201: {"description": "Comment submitted successfully."},
                500: {"description": "Failed to post comment."}
            }
)
async def log_recipe_feedback(feedback: RecipeComment):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{RECIPE_MANAGEMENT_BASE_URL}/recipes/{feedback.recipe_id}/feedback", json=feedback.dict())
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to post comment.")
    return {"message": "Comment logged successfully"}

@router.post("/search-history", 
             status_code=status.HTTP_201_CREATED,
             summary="Save search history",
             description="Save a user's search history.",
             responses={
                201: {"description": "Search history saved successfully."},
                500: {"description": "Failed to save search history."}
            }
)
async def save_search_history(search: SearchHistory):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_INTERACTION_BASE_URL}/search-history", json=search.dict())
        if response.status_code != 201:
            raise HTTPException(status_code=500, detail="Failed to save search history.")
    return {"message": "Search history saved successfully"}
 
RECIPE_MANAGEMENT_BASE_URL = "http://localhost:8001"  # Replace with actual URL
USER_INTERACTION_BASE_URL = "http://localhost:8002"   # Replace with actual URL
