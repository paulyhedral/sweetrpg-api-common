# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""
"""

from flask import current_app
from flask_rest_jsonapi.data_layers.base import BaseDataLayer
from flask_rest_jsonapi.exceptions import ObjectNotFound, JsonApiException
from sweetrpg_db.mongodb.repo import MongoDataRepository
from sweetrpg_db.mongodb.options import QueryOptions
from sweetrpg_db.utils import to_datetime
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from mongoengine import Document
from bson.objectid import ObjectId
import json
import logging


class APIData(BaseDataLayer):

    models = {}
    repos = {}

    def __init__(self, kwargs):
        """Intialize an data layer instance with kwargs
        :param dict kwargs: information about data layer instance
        """
        print("init: %s", kwargs)

        if kwargs.get("methods") is not None:
            self.bound_rewritable_methods(kwargs["methods"])
            kwargs.pop("methods")

        kwargs.pop("class", None)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return f"<APIData(type={self.type}, repos={self.repos}, models={self.models})>"

    @classmethod
    def _add_repo(cls, model_type: str, model_info: dict) -> None:
        if APIData.repos[model_type] is None:
            logging.info("Adding repository for type %s...", model_type)
            APIData.repos[model_type] = MongoDataRepository(
                model=model_info["model"], document=model_info["document"], collection=model_info["collection"]
            )
        else:
            logging.info("Repository already present for type %s.", model_type)

    @classmethod
    def set_models(cls, models: dict) -> None:
        logging.info("Replacing models...")
        APIData.models = models
        for model_type, model_info in models.items():
            APIData._add_repo(model_type, model_info)

    @classmethod
    def add_model(cls, name: str, model: dict) -> None:
        logging.info("Adding model %s...", name)
        APIData.models[name] = model
        APIData._add_repo(name, model)

    @classmethod
    def remove_model(cls, name: str) -> None:
        logging.info("Removing model %s...", name)
        del APIData.models[name]
        del APIData.repos[name]

    def create_object(self, data: dict, view_kwargs: dict) -> Document:
        """Create an object
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an object
        """
        # db = current_app.config["db"]
        # db = self.repos[self.type].db
        current_app.logger.debug("self: %s, data (%s): %s, view_kwargs: %s", self, data, type(data), view_kwargs)

        self.before_create_object(data, view_kwargs)

        json = data.to_dict()  # schema().dump(data, many=False)
        current_app.logger.info("self: %s, json: %s", self, json)

        try:
            repo = self.repos[self.type]
            current_app.logger.debug("self: %s, repo: %s", self, repo)
            obj_id = repo.create(json)
            current_app.logger.info("Object created with ID: %s", obj_id)
            current_app.logger.info("self: %s, obj: %s", self, obj)
        except DuplicateKeyError as dke:
            raise JsonApiException(dke.details, title="Duplicate key", status="409", code="duplicate-key")

        self.after_create_object(obj, data, view_kwargs)

        return obj

    def get_object(self, view_kwargs, qs=None):
        """Retrieve an object
        :params dict view_kwargs: kwargs from the resource view
        :params qs: A query string?
        :return DeclarativeMeta: an object
        """
        current_app.logger.debug("self: %s, view_kwargs: %s, qs: %s", self, view_kwargs, qs)

        # analytics.write()
        # analytics.identify("anonymous", {"name": "Michael Bolton", "email": "mbolton@example.com", "created_at": datetime.now()})

        self.before_get_object(view_kwargs)

        record_id = view_kwargs["id"]
        current_app.logger.info("Looking up record for ID '%s'...", record_id)
        repo = self.repos[self.type]
        current_app.logger.debug("self: %s, repo: %s", self, repo)
        try:
            record = repo.get(record_id)
            current_app.logger.info("self: %s, record: %s", self, record)
            if record is None:
                raise ObjectNotFound(f'No {self.type} record found for ID {view_kwargs["id"]}')
        except:
            raise ObjectNotFound(f'No {self.type} record found for ID {view_kwargs["id"]}')

        record = self.after_get_object(record, view_kwargs)
        current_app.logger.info("self: %s, record: %s", self, record)

        obj = models[self.type]["model"](**record)
        current_app.logger.info("self: %s, obj: %s", self, obj)

        return obj

    def get_collection(self, qs, view_kwargs, filters=None):
        """Retrieve a collection of objects
        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        :param dict filters: A dictionary of key/value filters to apply to the eventual query (ignored since it usually contains nothing)
        :return tuple: the number of objects and the list of objects
        """
        current_app.logger.debug("self: %s, qs: %s, view_kwargs: %s, filters: %s", self, qs, view_kwargs, filters)
        current_app.logger.debug("querystring: %s", qs.querystring)
        current_app.logger.debug(
            "fields: %s, sorting: %s, include: %s, pagination: %s, filters: %s", qs.fields, qs.sorting, qs.include, qs.pagination, qs.filters
        )

        self.before_get_collection(qs, view_kwargs)

        query = self.query(qs, view_kwargs)
        query = self.paginate_query(query, qs.pagination)

        repo = self.repos[self.type]
        current_app.logger.debug("self: %s, repo: %s", self, repo)
        objs = repo.query(query)
        current_app.logger.debug("self: %s, objs: %s", self, objs)

        collection = self.after_get_collection(objs, qs, view_kwargs)

        return len(collection), collection

    def update_object(self, obj, data, view_kwargs):
        """Update an object
        :param DeclarativeMeta obj: an object
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if object have changed else False
        """
        current_app.logger.debug("self: %s, obj: %s, data: %s, view_kwargs: %s", self, obj, data, view_kwargs)

        self.before_update_object(obj, data, view_kwargs)

        record_id = view_kwargs["id"]
        repo = self.repos[self.type]
        current_app.logger.debug("self: %s, repo: %s", self, repo)
        try:
            updated_record = repo.update(record_id, data)
            current_app.logger.debug("self: %s, updated_record: %s", self, updated_record)
        except:
            raise ObjectNotFound(f'Unable to delete {self.type} record for ID {view_kwargs["id"]}')

        self.after_update_object(updated_record, data, view_kwargs)

        return True

    def delete_object(self, obj, view_kwargs):
        """Delete an item through the data layer
        :param DeclarativeMeta obj: an object
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, obj: %s, view_kwargs: %s", self, obj, view_kwargs)

        self.before_delete_object(obj, view_kwargs)

        record_id = view_kwargs["id"]
        repo = self.repos[self.type]
        current_app.logger.debug("self: %s, repo: %s", self, repo)
        try:
            is_deleted = repo.delete(record_id)
            current_app.logger.debug("self: %s, is_deleted: %s", self, is_deleted)
        except:
            raise ObjectNotFound(f'Unable to delete {self.type} record for ID {view_kwargs["id"]}')

        self.after_delete_object(obj, view_kwargs)

        return is_deleted

    def create_relationship(self, json_data, relationship_field, related_id_field, view_kwargs):
        """Create a relationship
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if relationship have changed else False
        """
        current_app.logger.debug(
            "self: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            self,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )

        self.before_create_relationship(json_data, relationship_field, related_id_field, view_kwargs)

        # TODO
        obj = None
        updated = False

        self.after_create_relationship(obj, updated, json_data, relationship_field, related_id_field, view_kwargs)

        return obj, updated

    def get_relationship(self, relationship_field, related_type_, related_id_field, view_kwargs):
        """Get information about a relationship
        :param str relationship_field: the model attribute used for relationship
        :param str related_type_: the related resource type
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the object and related object(s)
        """
        current_app.logger.debug(
            "self: %s, relationship_field: %s, related_type_: %s, related_id_field: %s, view_kwargs: %s",
            self,
            relationship_field,
            related_type_,
            related_id_field,
            view_kwargs,
        )

        self.before_get_relationship(relationship_field, related_type_, related_id_field, view_kwargs)

        # TODO

        self.after_get_relationship(obj, related_objects, relationship_field, related_type_, related_id_field, view_kwargs)

        if isinstance(related_objects, InstrumentedList):
            return obj, [{"type": related_type_, "id": getattr(obj_, related_id_field)} for obj_ in related_objects]
        else:
            return obj, {"type": related_type_, "id": getattr(related_objects, related_id_field)}

    def update_relationship(self, json_data, relationship_field, related_id_field, view_kwargs):
        """Update a relationship
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if relationship have changed else False
        """
        current_app.logger.debug(
            "self: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            self,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )

        self.before_update_relationship(json_data, relationship_field, related_id_field, view_kwargs)

        # TODO
        obj = None
        updated = False

        self.after_update_relationship(obj, updated, json_data, relationship_field, related_id_field, view_kwargs)

        return obj, updated

    def delete_relationship(self, json_data, relationship_field, related_id_field, view_kwargs):
        """Delete a relationship
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug(
            "self: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            self,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )

        self.before_delete_relationship(json_data, relationship_field, related_id_field, view_kwargs)

        # TODO
        obj = None
        updated = False

        self.after_delete_relationship(obj, updated, json_data, relationship_field, related_id_field, view_kwargs)

        return obj, updated

    def query(self, qs, view_kwargs):
        """Construct the base query to retrieve wanted data
        :param QueryStringManager qs: the QueryStringManager
        :param dict view_kwargs: kwargs from the resource view
        :return QueryOptions: An initialized QueryOptions object
        """
        current_app.logger.debug("self: %s, qs: %s, view_kwargs: %s", self, qs, view_kwargs)

        query = QueryOptions()
        query.set_filters(from_querystring=qs.filters)
        # query.set_projection(from_querystring=qs.fields.get(self.type))
        query.set_sort(from_querystring=qs.sorting)

        return query

    def paginate_query(self, query, paginate_info):
        """Paginate query according to jsonapi 1.0
        :param QueryOptions query: MongoDB query options
        :param dict paginate_info: pagination information
        :return QueryOptions: an updated QueryOptions with pagination information
        """
        current_app.logger.debug("self: %s, query: %s, paginate_info: %s", self, query, paginate_info)

        if int(paginate_info.get("size", 1)) == 0:
            return query

        page_size = int(paginate_info.get("size", 0)) or current_app.config["PAGE_SIZE"]
        query.limit = page_size
        if paginate_info.get("number"):
            query.skip = (int(paginate_info["number"]) - 1) * page_size

        return query

    def _convert_properties(self, obj):
        current_app.logger.debug("self: %s, obj: %s", self, obj)

        date_properties = ["created_at", "updated_at", "deleted_at"]
        id_properties = ["_id", "id"]
        for p in date_properties + id_properties:
            current_app.logger.debug("self: %s, p: %s", self, p)

            try:
                property_value = obj.get(p) or getattr(obj, p)
            except:
                continue

            current_app.logger.debug("self: %s, property_value: %s", self, property_value)
            if property_value is None:
                continue

            if p in date_properties:
                current_app.logger.debug("self: %s, converting date property: %s, value: %s", self, p, property_value)
                new_property_value = to_datetime(property_value)
            elif p in id_properties:
                current_app.logger.debug("self: %s, converting ID property: %s, value: %s", self, p, property_value)
                if isinstance(property_value, dict):
                    new_property_value = property_value["$oid"]
                else:
                    new_property_value = str(property_value)

            if isinstance(obj, dict):
                obj[p] = new_property_value
            else:
                setattr(obj, p, new_property_value)

        current_app.logger.debug("self: %s, converted object: %s", self, obj)
        return obj

    def _populate_object(self, obj, properties):
        current_app.logger.debug("self: %s, obj: %s, properties: %s", self, obj, properties)

        for property_name, property_type in properties.items():
            current_app.logger.debug("self: %s, property_name: %s, property_type: %s", self, property_name, property_type)
            if not hasattr(obj, property_name) and not obj.get(property_name):
                continue
            property_value = obj.get(property_name) or getattr(obj, property_name)
            current_app.logger.debug("self: %s, property_value: %s", self, property_value)
            if property_value is None:
                continue
            if isinstance(property_value, str):
                current_app.logger.debug("self: %s, property_value is a string", self)

                new_property_value = self.repos[property_type].get(property_value)
                # current_app.logger.info("self: %s, new_value: %s", self, new_value)
                current_app.logger.debug("self: %s, new_property_value: %s", self, new_property_value)

                setattr(obj, property_name, new_property_value)

            if isinstance(property_value, list):
                current_app.logger.debug("self: %s, property_value is a list", self)

                new_property_value = []
                for list_value in property_value:
                    current_app.logger.debug("self: %s, list_value: %s", self, list_value)
                    if isinstance(list_value, dict):
                        value = list_value["$oid"]
                    else:
                        value = list_value
                    new_obj = self.repos[property_type].get(value)
                    current_app.logger.debug("self: %s, new_obj: %s", self, new_obj)
                    new_value = json.loads(new_obj.to_json())
                    current_app.logger.debug("self: %s, new_value: %s", self, new_value)
                    new_property_value.append(new_value)
                current_app.logger.debug("self: %s, new_property_value: %s", self, new_property_value)

                if isinstance(obj, dict):
                    obj[property_name] = new_property_value
                else:
                    setattr(obj, property_name, new_property_value)

        return obj

    def before_create_object(self, data, view_kwargs):
        """Provide additional data before object creation
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, data: %s, view_kwargs: %s", self, data, view_kwargs)

        delattr(data, "id")
        delattr(data, "deleted_at")
        now = datetime.utcnow()
        data.created_at = now
        data.updated_at = now

    def after_create_object(self, obj, data, view_kwargs):
        """Provide additional data after object creation
        :param obj: an object from data layer
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, %s, data: %s, view_kwargs: %s", self, obj, data, view_kwargs)

    def before_get_object(self, view_kwargs):
        """Make work before to retrieve an object
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, view_kwargs: %s", self, view_kwargs)

    def after_get_object(self, obj, view_kwargs):
        """Work after fetching an object, including fetching child objects
        :param obj: an object from data layer
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, obj: %s, view_kwargs: %s", self, obj, view_kwargs)

        this_model = models[self.type]
        current_app.logger.debug("self: %s, this_model: %s", self, this_model)
        properties = this_model.get("properties", {})
        current_app.logger.debug("self: %s, properties: %s", self, properties)

        data = json.loads(obj.to_json())
        current_app.logger.debug("self: %s, data: %s", self, data)
        converted_data = self._convert_properties(data)
        current_app.logger.debug("self: %s, converted_data: %s", self, converted_data)
        obj = self._populate_object(converted_data, properties)
        current_app.logger.debug("self: %s, obj: %s", self, obj)

        return obj

    def before_get_collection(self, qs, view_kwargs):
        """Make work before to retrieve a collection of objects
        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, qs: %s, view_kwargs: %s", self, qs, view_kwargs)

    def after_get_collection(self, collection, qs, view_kwargs):
        """Make work after to retrieve a collection of objects
        :param iterable collection: the collection of objects
        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, collection: %s, qs: %s, view_kwargs: %s", self, collection, qs, view_kwargs)

        this_model = models[self.type]
        current_app.logger.debug("self: %s, this_model: %s", self, this_model)
        properties = this_model.get("properties", {})
        current_app.logger.debug("self: %s, properties: %s", self, properties)

        updated_collection = []
        for obj in collection:
            data = json.loads(obj.to_json())
            current_app.logger.debug("self: %s, data: %s", self, data)
            converted_data = self._convert_properties(data)
            current_app.logger.debug("self: %s, converted_data: %s", self, converted_data)
            obj = converted_data  # self._populate_object(converted_data, properties)
            current_app.logger.debug("self: %s, obj: %s", self, obj)
            # current_app.logger.debug("self: %s, obj: %s", self, obj)
            # self._populate_object(obj, properties)
            updated_collection.append(obj)

        return updated_collection

    def before_update_object(self, obj, data, view_kwargs):
        """Make checks or provide additional data before update object
        :param obj: an object from data layer
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, obj: %s, data: %s, view_kwargs: %s", self, obj, data, view_kwargs)

    def after_update_object(self, obj, data, view_kwargs):
        """Make work after update object
        :param obj: an object from data layer
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, obj: %s, data: %s, view_kwargs: %s", self, obj, data, view_kwargs)

    def before_delete_object(self, obj, view_kwargs):
        """Make checks before delete object
        :param obj: an object from data layer
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, obj: %s, view_kwargs: %s", self, obj, view_kwargs)

    def after_delete_object(self, obj, view_kwargs):
        """Make work after delete object
        :param obj: an object from data layer
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug("self: %s, obj: %s, view_kwargs: %s", self, obj, view_kwargs)

    def before_create_relationship(self, json_data, relationship_field, related_id_field, view_kwargs):
        """Make work before to create a relationship
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if relationship have changed else False
        """
        current_app.logger.debug(
            "self: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s", self, relationship_field, related_id_field, view_kwargs
        )

    def after_create_relationship(self, obj, updated, json_data, relationship_field, related_id_field, view_kwargs):
        """Make work after to create a relationship
        :param obj: an object from data layer
        :param bool updated: True if object was updated else False
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if relationship have changed else False
        """
        current_app.logger.debug(
            "self: %s, obj: %s, update: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            self,
            obj,
            updated,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )

    def before_get_relationship(self, relationship_field, related_type_, related_id_field, view_kwargs):
        """Make work before to get information about a relationship
        :param str relationship_field: the model attribute used for relationship
        :param str related_type_: the related resource type
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the object and related object(s)
        """
        current_app.logger.debug(
            "self: %s, relationship_field: %s, related_type_: %s, related_id_field: %s, view_kwargs: %s",
            self,
            relationship_field,
            related_type_,
            related_id_field,
            view_kwargs,
        )

    def after_get_relationship(self, obj, related_objects, relationship_field, related_type_, related_id_field, view_kwargs):
        """Make work after to get information about a relationship
        :param obj: an object from data layer
        :param iterable related_objects: related objects of the object
        :param str relationship_field: the model attribute used for relationship
        :param str related_type_: the related resource type
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the object and related object(s)
        """
        current_app.logger.debug(
            "self: %s, obj: %s, update: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            self,
            obj,
            updated,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )

    def before_update_relationship(self, json_data, relationship_field, related_id_field, view_kwargs):
        """Make work before to update a relationship
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if relationship have changed else False
        """
        current_app.logger.debug(
            "self: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            self,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )

    def after_update_relationship(self, obj, updated, json_data, relationship_field, related_id_field, view_kwargs):
        """Make work after to update a relationship
        :param obj: an object from data layer
        :param bool updated: True if object was updated else False
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if relationship have changed else False
        """
        current_app.logger.debug(
            "self: %s, obj: %s, update: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            self,
            obj,
            updated,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )

    def before_delete_relationship(self, json_data, relationship_field, related_id_field, view_kwargs):
        """Make work before to delete a relationship
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug(
            "self: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            self,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )

    def after_delete_relationship(self, obj, updated, json_data, relationship_field, related_id_field, view_kwargs):
        """Make work after to delete a relationship
        :param obj: an object from data layer
        :param bool updated: True if object was updated else False
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        """
        current_app.logger.debug(
            "self: %s, obj: %s, update: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            self,
            obj,
            updated,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )
