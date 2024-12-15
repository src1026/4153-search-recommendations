from fastapi import APIRouter, HTTPException
from typing import List
from app.models.search_rec import SearchQuery, UserPreferences, SearchHistory, RecipeSection
from app.services.search_rec_service import SearchService, RecommendationService, UserPreferencesService
from framework.services.data_access.MySQLRDBDataService import MySQLRDBDataService
import asyncio

router = APIRouter()

# Configure DB
context = dict(
    user="jigglypuff7", 
    password="Jigglypuff7!",
    host="jigglypuff7.c7s86kaawl6v.us-east-2.rds.amazonaws.com", 
    port=3306,
    database="search_recommendation"
)
db_service = MySQLRDBDataService(context=context)
user_pref_service = UserPreferencesService(db_service)
search_service = SearchService(db_service)
recommendation_service = RecommendationService(db_service, user_pref_service)

@router.post("/search", response_model=List[RecipeSection])
async def search_recipes(query: SearchQuery):
    try:
        results = await search_service.search_recipes(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{user_id}", response_model=List[RecipeSection])
async def get_user_recommendations(user_id: int):
    try:
        results = await recommendation_service.get_recommendations(user_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preferences/{user_id}", response_model=UserPreferences)
def get_preferences(user_id: int):
    try:
        prefs = user_pref_service.get_user_preferences(user_id)
        return prefs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences/{user_id}")
def update_preferences(user_id: int, preferences: UserPreferences):
    try:
        user_pref_service.update_user_preferences(user_id, preferences)
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-history", status_code=201)
def save_search_history(search: SearchHistory):
    try:
        db_service.insert("search_history", {
            "user_id": search.user_id,
            "query": search.query,
            "created_at": "CURRENT_TIMESTAMP"
        })
        return {"message": "Search history saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))