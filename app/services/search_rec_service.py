import logging
import datetime
from typing import List
from app.models.search_rec import SearchQuery, UserPreferences, RecipeSection
import httpx

# Assuming you have a working MySQLRDBDataService class from your framework
from framework.services.data_access.MySQLRDBDataService import MySQLRDBDataService

RECIPE_MANAGEMENT_BASE_URL = "http://localhost:8001"
USER_INTERACTION_BASE_URL = "http://localhost:8002"

class UserPreferencesService:
    def __init__(self, db_service: MySQLRDBDataService):
        self.db = db_service
        self.logger = logging.getLogger(__name__)

    def get_user_preferences(self, user_id: int) -> UserPreferences:
        row = self.db.get_data_object(
            "user_preferences",
            conditions={"user_id": user_id}
        )
        if not row:
            return UserPreferences(exclude_ingredients=None, preferred_tags=None)

        exclude_ingredients = row.get("exclude_ingredients")
        preferred_tags = row.get("preferred_tags")

        if exclude_ingredients:
            exclude_ingredients = [x.strip() for x in exclude_ingredients.split(",") if x.strip()]

        if preferred_tags:
            preferred_tags = [x.strip() for x in preferred_tags.split(",") if x.strip()]

        return UserPreferences(exclude_ingredients=exclude_ingredients, preferred_tags=preferred_tags)

    def update_user_preferences(self, user_id: int, preferences: UserPreferences):
        exclude_str = ",".join(preferences.exclude_ingredients) if preferences.exclude_ingredients else None
        preferred_tags_str = ",".join(preferences.preferred_tags) if preferences.preferred_tags else None

        existing = self.db.get_data_object("user_preferences", conditions={"user_id": user_id})
        if existing:
            self.db.update("user_preferences", {"user_id": user_id}, 
                           data={"exclude_ingredients": exclude_str, "preferred_tags": preferred_tags_str})
        else:
            self.db.insert("user_preferences", {
                "user_id": user_id,
                "exclude_ingredients": exclude_str,
                "preferred_tags": preferred_tags_str
            })

class SearchService:
    def __init__(self, db_service: MySQLRDBDataService):
        self.db = db_service
        self.logger = logging.getLogger(__name__)

    async def search_recipes(self, query: SearchQuery) -> List[RecipeSection]:
        # Log the search
        self.db.insert("search_history", {
            "user_id": query.user_id,
            "query": " ".join(query.keywords),
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Fetch recipes from the recipe management service
        # Let's just fetch a batch of 100 recipes for simplicity
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECIPE_MANAGEMENT_BASE_URL}/recipes_sections", params={"offset":0, "limit":100})
            response.raise_for_status()
            data = response.json()
            recipes = [RecipeSection(**r) for r in data["data"]]

        # Filter by keywords: all keywords must appear in recipe_name or content
        if query.keywords:
            filtered = []
            for r in recipes:
                text = ((r.recipe_name or "") + " " + (r.content or "")).lower()
                if all(k.lower() in text for k in query.keywords):
                    filtered.append(r)
            recipes = filtered

        # Filter by ingredients: if ingredients provided, recipe must contain all
        if query.ingredients:
            filtered = []
            for r in recipes:
                if r.ingredient_id:
                    ingredients_list = [ing.strip().lower() for ing in r.ingredient_id.split(",")]
                    if all(ing.lower() in ingredients_list for ing in query.ingredients):
                        filtered.append(r)
            recipes = filtered

        return recipes

class RecommendationService:
    def __init__(self, db_service: MySQLRDBDataService, user_pref_service: UserPreferencesService):
        self.db = db_service
        self.user_pref_service = user_pref_service
        self.logger = logging.getLogger(__name__)

    async def get_recommendations(self, user_id: int) -> List[RecipeSection]:
        prefs = self.user_pref_service.get_user_preferences(user_id)

        # Fetch a batch of recipes
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECIPE_MANAGEMENT_BASE_URL}/recipes_sections", params={"offset":0, "limit":50})
            response.raise_for_status()
            data = response.json()
            recipes = [RecipeSection(**r) for r in data["data"]]

        # Exclude ingredients
        if prefs.exclude_ingredients:
            filtered = []
            for r in recipes:
                if r.ingredient_id:
                    ingredients = [ing.strip().lower() for ing in r.ingredient_id.split(",")]
                    if not any(e.lower() in ingredients for e in prefs.exclude_ingredients):
                        filtered.append(r)
                else:
                    filtered.append(r)
            recipes = filtered

        # If preferred_tags exist, promote recipes containing them
        # We'll sort by how many preferred tags appear in name or content
        if prefs.preferred_tags:
            def score(recipe: RecipeSection):
                text = ((recipe.recipe_name or "") + " " + (recipe.content or "")).lower()
                return sum(t.lower() in text for t in prefs.preferred_tags)

            recipes = sorted(recipes, key=score, reverse=True)

        return recipes[:10]