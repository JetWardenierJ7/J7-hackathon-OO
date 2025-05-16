"""This module facilitates all search interactions"""

from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from flask import request
from flask.views import MethodView
from schemas import PlainDocumentSchema, DefaultInputSchema, DefaultOutputSchema
from .resource_classes import ChunkSearchingClass, CL_Mistral_Embeddings, CL_Mistral_Completions

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
        completion = CL_Mistral_Completions().generate_completion(prompt)

        return {"output": completion}


@blp.route("/generate_document_summaries")
class GenerateDocumentSummaries(MethodView):
    """Generates summaries and indexes them"""

    @jwt_required()
    @blp.response(200)
    def post(self):
        payload = request.get_json()  # Ensure we get JSON data from the request
        completion_service = CL_Mistral_Completions()
        chunk_searcher = ChunkSearchingClass()
        data = payload.get("data", [])

        # Process all documents for the chunk_ids provided
        chunk_ids = [doc.get("chunk_id") for result in data for doc in result.get("documents", []) if doc.get("chunk_id")]
        
        for chunk_id in chunk_ids:
            try:
                # Get the complete document record from OpenSearch
                complete_record = chunk_searcher.get_by_id(chunk_id)
                print("Complete record: ", complete_record)
  
                content = complete_record.get("content_text", "").strip()

                # Ensure there is content to summarize
                if content:
                    # Create a summary for the document
                    prompt = f"Geef een samenvatting van de volgende tekst: {content} over het thema RijnlandRoute. Beschrijf kort wat de kern van de tekst is en wees concreet. Verzin geen zaken erbij. Begin je tekst NIET met 'De tekst beschrijft' of 'de inhoud van de tekst' zorg dat het een vloeiende tekst is. Deze tekst is bedoeld voor Statenleden, dus bepaald jargon over overheidstermologie mag gebruikt worden. Beperk je tot maximaal 4 a 5 zinnen. Vermijd vage en onnodige zinnen. Benoem alleen relevante zaken, als je echt niks inhoudelijk kan vinden, geef dat dan in één zin aan en omschrijf gewoon het onderwerp RijnlandRoute."
                    summary = completion_service.generate_summary(prompt)
                    print("Summary: ", summary)

                    # Update the document with the new summary
                    new_record = complete_record
                    new_record["summary"] = summary
                    print("New record: ", new_record)
                    # Insert updated document back into OpenSearch
                    chunk_searcher.update_document(index="es_hackathon", chunk_id=chunk_id, update_body=new_record)
            
            except Exception as e:
                print(f"Failed to update document {chunk_id}: {str(e)}")

        return {"results": [{"chunk_ids_processed": chunk_ids}]}