# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""
"""

from sweetrpg_api_core.data import APIData
from unittest.mock import patch, Mock
from flask_rest_jsonapi.querystring import QueryStringManager


class TestModel():
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {}


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


@patch('sweetrpg_db.mongodb.repo.MongoDataRepository.create')
def test_create(repo_create):

    repo_create.return_value = TestDocument()
    api = APIData({'type': 'test', 'db': None, 'model_info': model_info})
    model = api.create_object(TestModel(name="new"), {})

    assert isinstance(model, TestModel)


@patch('sweetrpg_db.mongodb.repo.MongoDataRepository.get')
def test_get_object(repo_get):

    repo_get.return_value = TestDocument()

    api = APIData({'type': 'test', 'db': None, 'model_info': model_info})
    obj = api.get_object({'id': "1"})

    assert isinstance(obj, TestModel)
    assert obj.id == "1"
    # TODO


@patch('sweetrpg_db.mongodb.repo.MongoDataRepository.query')
def test_get_collection(repo_query):

    repo_query.return_value = [TestDocument(), TestDocument()]

    api = APIData({'type': 'test', 'db': None, 'model_info': model_info})
    # TODO: need application context for QSM
    # count, objs = api.get_collection(QueryStringManager({'x':1}, None), {})
    #
    # assert count == 2
    # assert isinstance(objs[0], TestModel)


@patch('sweetrpg_db.mongodb.repo.MongoDataRepository.update')
def test_update_object(repo_update):

    repo_update.return_value = TestDocument()

    api = APIData({'type': 'test', 'db': None, 'model_info': model_info})
    is_updated = api.update_object(TestModel(), {"name": "new"}, {"id": "1"})

    assert is_updated == True


@patch('sweetrpg_db.mongodb.repo.MongoDataRepository.delete')
def test_delete_object(repo_delete):

    repo_delete.return_value = True

    api = APIData({'type': 'test', 'db': None, 'model_info': model_info})
    is_deleted = api.delete_object(TestModel(), {"id": "1"})

    assert is_deleted == True
