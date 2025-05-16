"""This module facilitates all search interactions"""

from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from flask.views import MethodView
from schemas import PlainDocumentSchema, SearchDocumentsSchema, SearchObjectsSchema
from .resource_classes import ChunkSearchingClass, CL_Mistral_Embeddings

blp = Blueprint("Search", "search", description="Operations on the search page")


@blp.route("/search_theme")
class SearchDocuments(MethodView):
    """Base search endpoint for random documents"""

    @jwt_required()
    @blp.arguments(SearchDocumentsSchema)
    # @blp.response(200, PlainDocumentSchema(many=True))
    @blp.response(200, SearchObjectsSchema(many=True))
    def post(self, input_data):
        """Gets the first 10 documents it can find in the OpenSearch index"""
        search_string = input_data["search_string"]
        search_config = {
            "search_string": search_string,
            "embedding": CL_Mistral_Embeddings().generate_embedding(search_string)
        }
        objects = ChunkSearchingClass().search_documents(search_config)
        
        # Aggregate all document IDs into a single list
        all_document_ids = [
            doc['document_id'] 
            for entry in objects 
            for doc in entry['documents']
        ]
        # Add the list of document IDs to the first entry
        if objects:
            objects[0]['document_ids'] = all_document_ids

        return objects