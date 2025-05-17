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
        data = payload.get("data", {})
        
        # Ensure timeline is a list within data
        timeline = data.get('timeline', [])
        if not isinstance(timeline, list):
            abort(400, message="Timeline must be a list")

        chunk_ids = []
        
        # Iterate over each timeline entry
        for entry in timeline:
            if not isinstance(entry, dict):
                continue

            documents = entry.get("documents", [])

            # Ensure documents is a list
            if not isinstance(documents, list):
                continue
            
            # Extract chunk_ids validating documents are dicts
            for doc in documents:
                if isinstance(doc, dict):
                    chunk_id = doc.get("chunk_id")
                    if chunk_id:
                        chunk_ids.append(chunk_id)

        # Proceed with processing the first chunk_id or handle empty case
        if chunk_ids:
            for chunk_id in chunk_ids:
                try:

                    # Get the complete document record from OpenSearch
                    complete_record = chunk_searcher.get_by_id(chunk_id)
                    # print("Complete record: ", complete_record)
                    
                    content = complete_record.get("content_text", "").strip()
                    document_title = complete_record["document_title"]
                    # Ensure there is content to summarize
                    if content:
                        # Create a summary for the document
                        prompt = f"Geef een samenvatting van de volgende tekst over het thema RijnlandRoute. Beschrijf kort wat de kern van de tekst is en wees concreet. Verzin geen zaken erbij. Begin je tekst NIET met 'De tekst beschrijft' of 'de inhoud van de tekst', ga meteen in op de inhoud en zorg dat het een vloeiende tekst is. Deze tekst is bedoeld voor Statenleden, dus bepaald jargon over overheidstermologie mag gebruikt worden. Beperk je tot maximaal 4 zinnen. Vermijd vage en onnodige zinnen.\n\n"
                        prompt += f"Het document {document_title}, de inhoud van het document is: {content}.\n\n"
                        prompt += f"Houd de tekst vloeiend, gebruik geen onnodige leestekens."
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
    

@blp.route("/generate_document_labels")
class GenerateDocumentSummaries(MethodView):
    """Generates summaries and indexes them"""

    @jwt_required()
    @blp.response(200)
    def post(self):
        payload = request.get_json()  # Ensure we get JSON data from the request
        completion_service = CL_Mistral_Completions()
        chunk_searcher = ChunkSearchingClass()
        data = payload.get("data", {})
        
        # Ensure timeline is a list within data
        timeline = data.get('timeline', [])
        if not isinstance(timeline, list):
            abort(400, message="Timeline must be a list")

        chunk_ids = []
        
        # Iterate over each timeline entry
        for entry in timeline:
            if not isinstance(entry, dict):
                continue

            documents = entry.get("documents", [])

            # Ensure documents is a list
            if not isinstance(documents, list):
                continue
            
            # Extract chunk_ids validating documents are dicts
            for doc in documents:
                if isinstance(doc, dict):
                    chunk_id = doc.get("chunk_id")
                    if chunk_id:
                        chunk_ids.append(chunk_id)
        
        for chunk_id in chunk_ids:
            try:
                # Get the complete document record from OpenSearch
                complete_record = chunk_searcher.get_by_id(chunk_id)
                print("Complete record: ", complete_record)

                content = complete_record.get("content_text", "").strip()
                summary = complete_record.get("summary", "")
                document_title = complete_record.get("document_title", "")
                type_primary = complete_record.get("type_primary", "")
                type_secondary = complete_record.get("type_secondary", "")

                # Ensure there is content to summarize
                if content:
                    # Create a summary for the document
                    prompt = f"""Je bent een expert op het gebied van overheidsdocumentatie. Je taak is om het type document te bepalen aan de hand van een titel of korte beschrijving. '
                    Geef ALLEEN de naam van het label terug, zonder onderbouwing. 
                    
                    De titel van het document is {document_title}.
                    De samenvatting is: {summary}.
                    en de content van een chunk van dit document is: {content}.

                    Het is VERPLICHT om enkel één van deze categorieën te kiezen. Geef ALLEEN de naam van de categorie terug:

                    Motie
                    Amendement 
                    Brief van derden 
                    Brief van Gedeputeerde Staten (GS) 
                    Verslag 
                    Statenvoorstel 
                    Nota
                    Overig"""
                    
                    label = completion_service.categorize_label(prompt)
         
                    # Update the document with the new summary
                    new_record = complete_record
                    new_record["label"] = label
                    print("New record: ", new_record)
                    
                    # Insert updated document back into OpenSearch
                    chunk_searcher.update_document(index="es_hackathon", chunk_id=chunk_id, update_body=new_record)
            
            except Exception as e:
                print(f"Failed to update document {chunk_id}: {str(e)}")

        return {"results": [{"chunk_ids_processed": chunk_ids}]}