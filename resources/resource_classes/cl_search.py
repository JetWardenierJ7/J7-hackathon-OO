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
    def get_chunks_for_chat(question, document_identifiers):
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
            "size": 10,
            "query": {
                "bool": {
                    "must": [
                        {
                            "terms": {
                                "document_id.keyword": document_identifiers
                            }
                        }
                    ],
                    "must": {
                        "knn": {
                            "content_embedding": {
                                "vector": question_embedding,
                                "k": 100
                            }
                        }
                    }
                }
            }
        }

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
    
    def search_documents(self, config):
        """Retrieves documents based on a search string"""

        body = {
                "size": 0, #size op 0, omdat je results in een aggregatie terugkomen
                "query": {
                    "knn": {
                        "content_embedding": {
                            "vector": config["embedding"],
                            "k": 100
                        }
                    }
                },
                "aggs": {
                    "Publicatiedatum": {
                        "terms": {
                            "field": "published",
                            "format":"yyyy-MM-dd",
                            "size":10000      
                        },  
                        "aggs": {
                            "Documents": {
                                "terms": {
                                    "field": "document_id.keyword",
                                    "size": 1000                       
                                },
                                "aggs": { #//met de code hieronder krijg je de top 5 chunks per document, gesorteerd op de score van je query. Let op: je krijgt per chunk alle informatie. Voor je frontend hoef je dus alleen het eerste deel te pakken
                                    "Document_Chunks": {
                                        "top_hits": {
                                            "size": 3, #//verhoog als je meer chunks wil zien binnen het document
                                            "sort": [
                                                {
                                                    "_score": {
                                                        "order": "desc"
                                                    }
                                                }
                                            ],
                                            "_source": {
                                                "excludes": [
                                                    "frontend.group*",
                                                    "content_embedding" #//embedding heb ik uit de respons gehaald. deze weghalen als je die wel wil zien
                                                ]
                                            }
                                        }
                                    },
                                    "max_score": {
                                        "max": {
                                            "script": {
                                                "source": "_score"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

        
        response = OPENSEARCH_CONNECTION.search(body=body, index="es_hackethon")

        objects_to_return = []
        for date_bucket in response["aggregations"]["Publicatiedatum"]["buckets"]:
            chunks_to_return = []
            date = date_bucket['key_as_string']
            
            for document_bucket in date_bucket['Documents']['buckets']:
                chunk = document_bucket["Document_Chunks"]["hits"]["hits"][0]
                chunks_to_return.append(chunk["_source"])

            object = {"date": date, "documents": chunks_to_return}
            objects_to_return.append(object)

        return objects_to_return
    
    def update_document(self, index, chunk_id, update_body):
        """
        Updates a document in the specified OpenSearch index.

        :param index: The index name where the document resides.
        :param document_id: The unique identifier of the document to update.
        :param update_body: The update body, usually a dictionary with a "doc" part.

        :return: The response of the update operation.
        """
        try:
            response = OPENSEARCH_CONNECTION.update(
                index="es_hackethon",
                id=chunk_id,    
                body={"doc": update_body}
            )
            return response
        except Exception as e:
            print(f"Failed to update document {chunk_id}: {str(e)}")
            return None
        
    def get_by_id(self, chunk_id):
        """
        Retrieves a document from the specified OpenSearch index by its unique identifier.

        :param index: The index name where the document resides.
        :param document_id: The unique identifier of the document to retrieve.

        :return: The document record.
        """
        try:
            response = OPENSEARCH_CONNECTION.search(
                index="es_hackethon", 
                body={"query": {"bool": {"must": [{"term": {"chunk_id.keyword": chunk_id}}]}}}
            )
            hits = response['hits']['hits']
            if hits:
                return hits[0]["_source"]
            return None
        except Exception as e:
            print(f"Failed to retrieve document {chunk_id}: {str(e)}")
            return None