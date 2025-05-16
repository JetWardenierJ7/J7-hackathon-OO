"""Resource class for searching though OpenSearch indices"""

import os
from opensearchpy import OpenSearch
from dotenv import load_dotenv
from resources.resource_classes.cl_mistral_connection import CL_Mistral_Embeddings

load_dotenv()

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")
OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")

OPENSEARCH_CONNECTION = OpenSearch(
    OPENSEARCH_URL,
    http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
    request_timeout=900,
    verify_certs=False,
)


class ChunkSearchingClass:
    """Simple class for searching `Chunk` objects"""

    def __init__(self):
        pass

    def search(self):
        """Retrieves 10 random documents from our index"""

        chunks_to_return = []
        response = OPENSEARCH_CONNECTION.search(body={"size": 10}, index="es_hackethon")

        for chunk in response["hits"]["hits"]:
            chunks_to_return.append(chunk["_source"])

        return chunks_to_return

    def get_documents_for_timeline(self):
        """Retrieves all the related document identifiers"""
        document_ids = [self.document_identifier]

        return document_ids

    @staticmethod 
    def get_chunks_for_chat(question):
        """
        Retrieves relevant document chunks for a given opportunity and question.

        This method performs a hybrid search using question embeddings and retrieves
        chunks of text from documents associated with the specified opportunity. The
        search leverages Elasticsearch's k-NN capabilities to find the most relevant
        document segments.

        :param document_ids:
            A list of document identifiers to search through

        :param question:
            The question for which relevant document chunks are to be retrieved.
            An embedding of the question is generated for k-NN search.

        :returns:   A list of text chunks from the documents that are relevant to the given question.
                    Returns an empty list if no opportunity is found or if no relevant chunks are identified.
        :rtype: list

        """
        # Step 1. Generate embedding from question
        question_embedding = (
            CL_Mistral_Embeddings().generate_embedding(question)
        )

        # Step 2. Retrieve chunks based on KNN search
        es_query = {
            "size":10,
            "query" : {
                
                    "knn": {
                        "content_embedding": {
                            "vector":question_embedding,
                            "k": 10
                        }
                    }
                }
        }


        # print("Es query ; ", es_query)
        # Step 3. Return relevant chunks to base answer on
        response = OPENSEARCH_CONNECTION.search(
            index="es_hackethon",
            body=es_query,
        )
        chunks = [
            hit["_source"]["content_text"]
            for hit in response["hits"]["hits"]
        ]

        return chunks
