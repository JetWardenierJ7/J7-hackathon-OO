"""Resource class for searching though OpenSearch indices"""

import os
from opensearchpy import OpenSearch
from dotenv import load_dotenv

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
