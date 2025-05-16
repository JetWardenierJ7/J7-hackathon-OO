"""This module facilitates all search interactions"""

from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from flask.views import MethodView
from schemas import PlainDocumentSchema, SearchDocumentsSchema, SearchObjectsSchema, SearchResultsSchema
from .resource_classes import ChunkSearchingClass, CL_Mistral_Embeddings

blp = Blueprint("Search", "search", description="Operations on the search page")


@blp.route("/search_theme")
class SearchDocuments(MethodView):
    """Base search endpoint for random documents"""

    @jwt_required()
    @blp.arguments(SearchDocumentsSchema)
    # @blp.response(200, PlainDocumentSchema(many=True))
    @blp.response(200, SearchResultsSchema)
    def post(self, input_data):
        """Gets the first 10 documents it can find in the OpenSearch index"""
        search_string = input_data["search_string"]

        

        search_config = {
            "search_string": search_string,
            "embedding": CL_Mistral_Embeddings().generate_embedding(search_string)
        }

        if input_data.get("search_from"): 
            search_config["search_from"]=input_data.get("search_from")

        if input_data.get("search_until"): 
            search_config["search_until"]=input_data.get("search_until")

        if input_data.get("publisher"): 
            search_config["publisher"]=input_data.get("publisher_types")

        if input_data.get("type_primary"): 
            search_config["type_primary"]=input_data.get("type_primary")

        objects, filters = ChunkSearchingClass().search_documents(search_config)

        return {"timeline": objects, "filters": filters}