"""This module facilitates all search interactions"""

from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from flask.views import MethodView
from schemas import PlainDocumentSchema, SearchDocumentsSchema, SearchObjectsSchema, SearchResultsSchema
from .resource_classes import ChunkSearchingClass, CL_Mistral_Embeddings, CL_Mistral_Completions

blp = Blueprint("Search", "search", description="Operations on the search page")


@blp.route("/search_theme")
class SearchDocuments(MethodView):
    """Base search endpoint for random documents"""

    @jwt_required()
    @blp.arguments(SearchDocumentsSchema)
    # @blp.response(200, SearchObjectsSchema(many=True))
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
            search_config["publisher"]=input_data.get("publisher")

        if input_data.get("type_primary"): 
            search_config["type_primary"]=input_data.get("type_primary")

        if input_data.get("type_secondary"): 
            search_config["type_secondary"]=input_data.get("type_secondary")

        objects, filters = ChunkSearchingClass().search_documents(search_config)
        print("Objects: ", objects)
        # Aggregate all document IDs into a single list
        all_document_ids = [
            doc['document_id'] 
            for entry in objects 
            for doc in entry['documents']
        ]
        
        if objects:
            objects[0]['document_ids'] = all_document_ids

        # Generate summaries if the search string is not "RijnlandRoute"
        if search_string != "RijnlandRoute":
            summaries = []
            for entry in objects[:1]:
                doc_count = 0
                for doc in entry['documents']:
                    if doc_count >= 3:
                        break
                    content_text = doc['content_text']
                    print("Content text: ", content_text)
                    print("Docid: ", doc['document_id'])
                    prompt = f"Geef een samenvatting van de volgende tekst: {content_text} over het thema {search_string}. Beschrijf kort wat de kern van de tekst is en wees concreet. Verzin geen zaken erbij. Begin je tekst NIET met 'De tekst beschrijft' of 'de inhoud van de tekst' zorg dat het een vloeiende tekst is. Deze tekst is bedoeld voor Statenleden, dus bepaald jargon over overheidstermologie mag gebruikt worden. Beperk je tot maximaal 4 a 5 zinnen. Vermijd vage en onnodige zinnen. Benoem alleen relevante zaken, als je echt niks inhoudelijk kan vinden, geef dat dan in één zin aan en omschrijf gewoon het onderwerp RijnlandRoute."
                    
                    summary = CL_Mistral_Completions().generate_summary(prompt)
                    print("Generating summary for document: ", doc)
                    doc['summary'] = summary
                    doc_count += 1


        return {"timeline": objects, "filters": filters}