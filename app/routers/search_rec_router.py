from fastapi import APIRouter, Depends

from app.models.search_rec import SearchQuery
from app.services.search_rec_service import SearchService, RecommendationService

router = APIRouter()
search_service = SearchService()
recommendation_service = RecommendationService()

@router.get("/search/")
async def search_recipes(search_query: SearchQuery):
    return search_service.search_recipes(search_query)
    # TODO Do lifecycle management for singleton resource

@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int):
    return recommendation_service.get_recommendations(user_id)