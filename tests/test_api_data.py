# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""
"""

from sweetrpg_api_core.data import APIData
from unittest.mock import patch, Mock


class TestModel():
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)


class TestDocument():
    def to_json(self):
        return r'{"id":"1"}'

model_info = {
    "test": {
        "model": TestModel,
        "document": TestDocument,
        "type": "test",
        "collection": "tests",
        "properties": {},
    },
}


def test_create():
    # api = APIData()
    # data = {}
    pass


@patch('sweetrpg_db.mongodb.repo.MongoDataRepository.get')
def test_get_object(repo_get):

    repo_get.return_value = TestDocument()

    api = APIData({'type': 'test', 'db': None, 'model_info': model_info})
    obj = api.get_object({'id': "1"})

    assert isinstance(obj, TestModel)
    assert obj.id == "1"
    # TODO


def test_get_collection():
    pass


def test_update_object():
    pass


def test_delete_object():
    pass
