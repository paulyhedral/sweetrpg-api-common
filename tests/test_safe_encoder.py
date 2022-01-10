# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""
"""

from sweetrpg_api_core.utils import SafeEncoder
from bson.timestamp import Timestamp
import json


def test_encode_timestamp():
    data = {
        'key': 'value',
        'list': [
            Timestamp(0, 0),
        ]
    }

    e = json.dumps(data, cls=SafeEncoder)
    d = json.loads(e)

    assert isinstance(e, str)
    assert isinstance(d, dict)
    assert len(d['list']) == 1
    assert isinstance(d['list'][0], str)


def test_encode_bytes():
    data = {
        'key': 'value',
        'bytes': 'some text'.encode('utf-8')
    }

    e = json.dumps(data, cls=SafeEncoder)
    d = json.loads(e)

    assert isinstance(e, str)
    assert isinstance(d, dict)
    assert isinstance(d['bytes'], str)
