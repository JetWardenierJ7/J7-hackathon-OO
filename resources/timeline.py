"""This module facilitates all search interactions"""

from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from flask.views import MethodView
from schemas import PlainDocumentSchema, DefaultInputSchema, DefaultOutputSchema
from .resource_classes import ChunkSearchingClass, CL_Mistral_Connection

blp = Blueprint("Timeline", "timelineh", description="Operations on the timeline page")


@blp.route("/completion")
class Completion(MethodView):
    """Base completions endpoint"""

    @jwt_required()
    @blp.arguments(DefaultInputSchema)
    @blp.response(200, DefaultOutputSchema)
    def post(self, input_data):
        """Answers a prompt"""

        prompt = input_data["input"]
        completion = CL_Mistral_Connection().generate_completion(prompt)

        return {"output": completion}
