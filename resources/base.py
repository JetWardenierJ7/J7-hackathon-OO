"""Base resource module"""

from flask import send_file, redirect
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from opensearchpy import OpenSearch

import os
import requests
import mimetypes


blp = Blueprint("Base", "base", description="Operations on the base endpoint")

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")
OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")

OPENSEARCH_CONNECTION = OpenSearch(
    OPENSEARCH_URL,
    http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
    request_timeout=900,
    verify_certs=False,
)
DOCUMENT_INDEX = "es_hackethon"


@blp.route("/")
class BaseRouteClass(MethodView):
    """Used to test if the container is booted up"""

    def get(self):
        return "Bonjour", 200


@blp.route("/download/<string:document_identifier>")
class DocumentDownloadClass(MethodView):
    """Responsible for downloading the document"""

    def get(self, document_identifier):
        """Download the document"""

        doc = HackathonDocument.from_opensearch(document_identifier)

        dest_folder = "./data/tmp"
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)  # create folder if it does not exist

        print("doc: ", doc, flush=True)

        url = None
        if doc["type_primary"] == "Raadsverslag": 
            url = "https://joinseven.nl/download/index.php?url="+doc["document_url"]+"&title="+doc["document_title"]
        if doc["type_primary"] == "Provinciaal verslag": 
            url = "https://joinseven.nl/download/index.php?url="+doc["document_url"]+"&title="+doc["document_title"]
        elif doc["type_primary"] == "Kamerstuk": 
            url = doc["document_url"]


        if url: 
            r = requests.get(url, stream=True, timeout=18000)

            if "content-type" in r.headers:
                content_type = r.headers["content-type"]
                extension = mimetypes.guess_extension(content_type)
            else:
                extension = doc["extension"]
                if extension[0] != ".":
                    extension = "." + extension

            file_path = os.path.join(dest_folder, doc["document_id"] + extension)

            if r.ok:
                print("saving to", os.path.abspath(file_path))
                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 8):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                            os.fsync(f.fileno())
                return send_file(file_path, as_attachment=True)
            else:  # HTTP status code 4XX/5XX
                print(f"Download failed: status code {r.status_code}\n{r.text}")
                return False
            
        else: 
            return doc["url"]



class HackathonDocument:
    """Represents a `Document` instance"""


    @classmethod
    def from_opensearch(cls, document_identifier):
        """Initializes a new `HackathonDocument` instancy from it's identifier

        :param document_identifier:
            The unique identifier of the `HeptagonDocument`

        :returns: A `HeptagonDocument` instance
        :rtype: `HeptagonDocument`
        """

        document_body = {
            "query": {
            "bool": {
                "must": [{"term": {"document_id": document_identifier}}]
            }
            }
        }

        elastic_response = OPENSEARCH_CONNECTION.search(
            size=1, index=DOCUMENT_INDEX, body=document_body
        )

        if elastic_response["hits"]["total"]["value"] == 0:
            return False

        elastic_document_base = elastic_response["hits"]["hits"][0]["_source"]

        return elastic_document_base
