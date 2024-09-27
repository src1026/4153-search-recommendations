from app.models.search_rec import SearchQuery, Recommendation

class SearchService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        self.table = self.dynamodb.Table('SearchQueries')

    def search_recipes(self, search_query: SearchQuery):
        self.table.put_item(Item=search_query.dict())
        # TODO: search algorithm??
        return {"recipes": ["Recipe1", "Recipe2"]}

class RecommendationService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        self.table = self.dynamodb.Table('Recommendations')

    def get_recommendations(self, user_id: int):
        response = self.table.get_item(Key={'user_id': user_id})
        return response.get('Item', {"recommended_recipes": []})