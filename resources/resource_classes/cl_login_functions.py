"""This module contains classes used by the login process"""

import re
from datetime import datetime
from datetime import timedelta
from db import db
from elasticsearch import Elasticsearch
import certifi


class LoginRequirements:
    """This class is responsible for checking if a login meets the requirements"""

    def __init__(self, password):
        self.password = password

    def check_password(self):
        """Checks if the password meets the requirements"""

        checks = {
            "length": {
                "passed": len(self.password) >= 9,
                "message": "Password should be at least 9 characters long.",
            },
            "uppercase": {
                "passed": re.search(r"[A-Z]", self.password) is not None,
                "message": "Password should contain at least one uppercase letter.",
            },
            "special_char": {
                "passed": re.search(r"[!@#$%^&*]", self.password) is not None,
                "message": "Password should contain at least one special character.",
            },
            "number": {
                "passed": re.search(r"\d", self.password) is not None,
                "message": "Password should contain at least one number.",
            },
        }

        return {k: v for k, v in checks.items() if not v["passed"]}


class LastLogin:

    esConnection = Elasticsearch(
        "https://be00d451564e4a808d79d7e5f061760a.westeurope.azure.elastic-cloud.com:9243",
        basic_auth=("elastic", "exBpmFlMVnuZNItT9MuPPcHD"),
        ca_certs=certifi.where(),
        request_timeout=900,
    )

    @staticmethod
    def is_longer_than_7_days_ago(last_login_date):
        """Checks if the last_login date is greater than 7 days ago"""
        seven_days_ago = datetime.now() - timedelta(days=7)

        if last_login_date < seven_days_ago:
            return True

        return False

    @staticmethod
    def get_remote_address(user_data, request):
        """Retrieves the remote address"""
        remote_addr = None
        if user_data.get("ip_address"):
            remote_addr = user_data.get("ip_address")
        else:
            if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
                remote_addr = request.environ["REMOTE_ADDR"]
            else:
                remote_addr = request.environ["HTTP_X_FORWARDED_FOR"]

        return remote_addr

    @staticmethod
    def get_published_opportunities(user_id, company_id, last_login_date):
        """Retrieves count and identifiers of opportunities published after the last login date"""
        seven_days_ago = datetime.now() - timedelta(days=7)
        # one_second_ago = datetime.now() - timedelta(seconds=1)
        if last_login_date < seven_days_ago:
            last_login_formatted = last_login_date.strftime("%Y-%m-%d %H:%M:%S")

            # Query Elasticsearch for opportunities published after the last login date
            query = {
                "bool": {
                    "must": [
                        {"term": {"company_id": company_id}},
                        {"range": {"created_at": {"gte": last_login_formatted}}},
                    ]
                }
            }
            result = LastLogin.esConnection.search(
                index="es_opportunities",
                query=query,
                size=1000,  # Adjust this value based on your needs
            )

            count = result["hits"]["total"]["value"]
            identifiers = [
                hit["_source"]["identifier"] for hit in result["hits"]["hits"]
            ]

            return count, identifiers
        return 0, []
