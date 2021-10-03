# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""
exceptions.py
- API exceptions
"""


from werkzeug.exceptions import HTTPException


def error_response(response_class, code: str, message: str, attribute: str = None):
    response = {
        "code": code,
        "attribute": attribute,
        "message": message,
    }

    raise response_class(response=response)
