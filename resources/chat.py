from schemas import ChatInputSchema
from flask import abort, Response, Blueprint, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt
from flask_smorest import Blueprint, abort, error_handler
from flask.views import MethodView
from models import UserModel
from resources.resource_classes import ChunkSearchingClass
from resources.resource_classes.cl_mistral_connection import CL_Mistral_Completions

blp = Blueprint(
    "Chat", "chat", description="Chatoperations on timelines"
)
@blp.route("/timeline/chat")
class OpportunityChatEndpoint(MethodView):
    """Provides chat functionality on a specific opportunity."""

    @jwt_required()
    @blp.arguments(ChatInputSchema)
    @blp.alt_response(
        404,
        schema=error_handler.ErrorSchema,
        description="The `Timeline` object could not be found.",
    )
    def post(self, chat_data):
        """Handles chat questions related to a timeline

        This method enables chat interactions for an opportunity, leveraging AI to answer
        questions based on the timeline data, and streams the response back to the user.

        :param chat_data:
            The question or chat data for the opportunity

        :param timeline_id:
            The identifier of the `Opportunity` to which the chat relates

        :returns: A stream response of the answer to the chat question
        :rtype: Response (mimetype: text/plain)

        :raises 404 Not found:
            The `Opportunity` object could not be found

        """
        user: UserModel = UserModel.query.get_or_404(get_jwt()["sub"])

        ## Haal tijdlijn op uit OpenSearch
        # es_timeline = ChunkSearchingClass.from_opensearch(timeline_id)
        chat_history = []
        # Get document identifiers for timeline
        # documents = ChunkSearchingClass.get_documents_for_timeline(timeline_id)

        # Get chunks from documents
        chunks = ChunkSearchingClass.get_chunks_for_chat(chat_data["question"])

        prompt = f"Geef antwoord op de gestelde vraag: {chat_data["question"]} op basis van de volgende context: {chunks}"
        completion = CL_Mistral_Completions().chat_response(prompt)
        # stream = CL_Mistral_Completions("").chat_response(
        #     chat_history, chat_data["question"], chunks, prompt
        # )

        return {"output": completion}
