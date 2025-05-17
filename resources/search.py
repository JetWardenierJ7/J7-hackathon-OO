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
        
        # Aggregate all document IDs into a single list
        all_document_ids = [
            doc['document_id'] 
            for entry in objects 
            for doc in entry['documents']
        ]
        
        if objects:
            objects[0]['document_ids'] = all_document_ids

        # Generate summaries if the search string is not "RijnlandRoute"
        if search_string.lower() not in ["rijnlandroute", "windpark spui"]:
            summaries = []
            for entry in objects[:3]:
                doc_count = 0
                for doc in entry['documents']:
                    document_title = doc['document_title']
                    content_text = doc['content_text']
                    if doc_count >= 3:
                        break
                   
                    # print("Content text: ", content_text)
                    # print("Docid: ", doc['document_id'])
                    summary_prompt = f"Geef een samenvatting van de volgende tekst: {content_text} over het thema {search_string}. Beschrijf kort wat de kern van de tekst is en wees concreet."
                  
                    summary = CL_Mistral_Completions().generate_summary(summary_prompt)

                    label_prompt = f"""Je bent een expert op het gebied van overheidsdocumentatie. Je taak is om het type document te bepalen aan de hand van een titel of korte beschrijving. '
                    Geef ALLEEN de naam van het label terug, zonder onderbouwing. 
                    
                    De titel van het document is {document_title}.
                    De samenvatting is: {summary}.
                    en de content van een chunk van dit document is: {content_text}.

                    Het is VERPLICHT om enkel één van deze categorieën te kiezen. Een andere categorie is NIET toegestaan.Geef ALLEEN de naam van de categorie terug:


                    Motie
                    Amendement 
                    Brief van derden 
                    Brief van Gedeputeerde Staten (GS) 
                    Verslag 
                    Statenvoorstel 
                    Nota
                    Overig
                    """
                    label = CL_Mistral_Completions().categorize_label(label_prompt)
                    print("Generating summary for document: ", doc)
                    doc['summary'] = summary
                    doc['label'] = label
                    doc_count += 1


        return {"timeline": objects, "filters": filters}