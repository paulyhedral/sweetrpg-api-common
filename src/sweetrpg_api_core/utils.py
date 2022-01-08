# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""utils.py
Various utility classes and functions
"""

import json
from typing import Any
from bson.timestamp import Timestamp


class SafeEncoder(json.JSONEncoder):
    """
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, Timestamp):
            return str(o.as_datetime())
        return json.JSONEncoder.default(self, o)
