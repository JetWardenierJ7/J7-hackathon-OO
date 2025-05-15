"""This module facilitates all search interactions"""

from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from flask.views import MethodView
from schemas import PlainDocumentSchema
from .resource_classes import ChunkSearchingClass

blp = Blueprint("Search", "search", description="Operations on the search page")


@blp.route("/search")
class SearchDocuments(MethodView):
    """Base search endpoint for random documents"""

    @jwt_required()
    @blp.response(200, PlainDocumentSchema(many=True))
    def get(self):
        """Gets the first 10 documents it can find in the OpenSearch index"""

        chunks = ChunkSearchingClass().search()

        return chunks
