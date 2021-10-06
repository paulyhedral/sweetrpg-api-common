# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""API exceptions
"""

from werkzeug.exceptions import HTTPException


def error_response(response_class, code: str, message: str, attribute: str = None):
    """Generates an instance of the response class, filled in with the specified
    code, message, and attribute.

    Args:
        response_class: A class type to instantiate.
        code (str): The code value to put in the object.
        message (str): The message to put in the object.
        attribute (str, optional): [description]. Defaults to None.

    Raises:
        response_class: [description]
    """
    response = {
        "code": code,
        "attribute": attribute,
        "message": message,
    }

    raise response_class(response=response)
