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
        

        #Filter on date
        range_filter = {}
        if "search_from" in config:
            range_filter["gte"] = config["search_from"]
        if "search_until" in config:
            range_filter["lt"] = config["search_until"]
        filters = []
        if range_filter:
            filters.append({
                "range": {
                    "published": range_filter
                }
            })

        #Filter on publisher ("Provincie", "Gemeente", "Tweede Kamer", "Hoogheemraadschap", "Waterschap")
        publisher_types = config.get("publisher_types", [])

        if publisher_types:
            filters.append({
                "terms": {
                    "publisher.keyword": publisher_types
                }
            })

            # filters.append({
            #     "bool": {
            #         "should": [
            #             {"prefix": {"publisher.keyword": f"{t} "}} for t in publisher_types
            #         ],
            #         "minimum_should_match": 1
            #     }
            # })

        #Filter on type primary ("Provinciaal verslag", "Vergadering", "Raadsverslag", "Kamerstuk", "waterschap vergadering", "Bijlage", "Kamervragen (Aanhangsel)")
        type_primary = config.get("type_primary", [])

        if type_primary:
            filters.append({
                "terms": {
                    "type_primary.keyword": type_primary
                }
            })

        #Filter on type primary ("Provinciaal verslag", "Vergadering", "Raadsverslag", "Kamerstuk", "waterschap vergadering", "Bijlage", "Kamervragen (Aanhangsel)")
        type_secondary = config.get("type_secondary", [])

        if type_secondary:
            filters.append({
                "terms": {
                    "type_secondary.keyword": type_secondary
                }
            })

        aggs = {
            "Publicatiedatum": {
                "date_histogram": {
                    "field": "published",
                    "calendar_interval": "day",
                    "format": "yyyy-MM-dd",
                    "order": {
                        "_key": "desc"
                    },
                    "min_doc_count": 1
                },
                "aggs": {
                    "Documents": {
                        "terms": {
                            "field": "document_id.keyword",
                            "size": 1000
                        },
                        "aggs": {
                            "Document_Chunks": {
                                "top_hits": {
                                    "size": 1,
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
                                            "content_embedding"
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
            },
            "type_primary": {
                "terms": {
                    "field": "type_primary.keyword",
                    "size": 1000
                }
            },
            "publisher_types": {
                "terms": {
                    "field": "publisher.keyword",
                    "size": 1000
                }
            },
            "type_secondary": {
                "terms": {
                    "field": "type_secondary.keyword",
                    "size": 1000
                }
            }
        }




        query = {
            "bool": {
                "must": {
                    "knn": {
                        "content_embedding": {
                            "vector": config["embedding"],
                            "k": 100
                        }
                    }
                },
                "filter": filters  # dit is [] als er geen datumfilter is
            }
        }


        body = {
            "size": 0,
            "query": query,
            "aggs": aggs
        }



        
        response = OPENSEARCH_CONNECTION.search(body=body, index="es_hackethon")

        print('response: ', response, flush=True)

        objects_to_return = []
        for date_bucket in response["aggregations"]["Publicatiedatum"]["buckets"]:
            chunks_to_return = []
            date = date_bucket['key_as_string']
            
            for document_bucket in date_bucket['Documents']['buckets']:
                chunk = document_bucket["Document_Chunks"]["hits"]["hits"][0]
                chunks_to_return.append(chunk["_source"])

            object = {"date": date, "documents": chunks_to_return}
            objects_to_return.append(object)

        type_primary = []
        if len(response["aggregations"]["type_primary"]["buckets"]) > 0:
            for aggregation_results in response["aggregations"]["type_primary"][
                "buckets"
            ]:
                type_primary.append(
                    {
                        "type_primary": aggregation_results["key"],
                        "amount_of_docs": aggregation_results["doc_count"],
                    }
                )

        publishers = []
        if len(response["aggregations"]["publisher_types"]["buckets"]) > 0:
            for aggregation_results in response["aggregations"]["publisher_types"][
                "buckets"
            ]:
                publishers.append(
                    {
                        "publisher": aggregation_results["key"],
                        "amount_of_docs": aggregation_results["doc_count"],
                    }
                )

        type_secondary = []
        if len(response["aggregations"]["type_secondary"]["buckets"]) > 0:
            for aggregation_results in response["aggregations"]["type_secondary"][
                "buckets"
            ]:
                type_secondary.append(
                    {
                        "type_secondary": aggregation_results["key"],
                        "amount_of_docs": aggregation_results["doc_count"],
                    }
                )

        filters = {
            "type_primary": type_primary, 
            "type_secondary": type_secondary, 
            "publishers": publishers
        }

        return objects_to_return, filters
