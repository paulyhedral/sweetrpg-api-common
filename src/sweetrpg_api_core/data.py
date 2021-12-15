# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""API data abstraction.
"""

from flask import current_app
from flask_rest_jsonapi.data_layers.base import BaseDataLayer
from flask_rest_jsonapi.exceptions import ObjectNotFound, JsonApiException
from sweetrpg_db.mongodb.repo import MongoDataRepository
from sweetrpg_db.mongodb.options import QueryOptions
from sweetrpg_model_core.convert.date import to_datetime
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from mongoengine import Document
from bson.objectid import ObjectId
from sweetrpg_model_core.model.base import BaseModel
from sweetrpg_model_core.convert.document import to_model
from sweetrpg_model_core.convert.model import to_document
import json
import logging


class APIData(BaseDataLayer):
    """

    """

    def __init__(self, kwargs):
        """Initialize a data layer instance with kwargs.

        :param dict kwargs: information about data layer instance
        """
        logging.debug("init: %s", kwargs)

        if kwargs.get("methods") is not None:
            self.bound_rewritable_methods(kwargs["methods"])
            kwargs.pop("methods")

        kwargs.pop("class", None)

        self.repos = {}
        for key, value in kwargs.items():
            setattr(self, key, value)

        for model_type, model_info in self.model_info.items():
            logging.info("Adding repository for type %s...", model_type)
            self.repos[model_type] = MongoDataRepository(
                model=model_info["model"], document=model_info["document"], collection=model_info["collection"]
            )

    def __repr__(self) -> str:
        return f"<APIData(type={self.type}, repos={self.repos}, model_info={self.model_info})>"

    def create_object(self, model: BaseModel, view_kwargs: dict) -> Document:
        """Create an object.

        :param BaseModel model: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an object
        """
        # db = current_app.config["db"]
        # db = self.repos[self.type].db
        logging.debug("data (%s): %s, view_kwargs: %s", model, type(model), view_kwargs)

        self.before_create_object(model, view_kwargs)

        data = model.to_dict()
        logging.debug("data: %s", data)

        try:
            repo = self.repos[self.type]
            logging.debug("repo: %s", repo)
            doc = repo.create(data)
            logging.info("Document created: %s", doc)
            model_class = self.model_info[self.type]["model"]
            logging.debug("model_class: %s", model_class)
            new_model = to_model(doc, model_class)
            logging.debug("new_model: %s", new_model)
        except DuplicateKeyError as dke:
            raise JsonApiException(dke.details, title="Duplicate key", status="409", code="duplicate-key")

        self.after_create_object(new_model, data, view_kwargs)

        return new_model

    def get_object(self, view_kwargs, qs=None):
        """Retrieve an object
        :params dict view_kwargs: kwargs from the resource view
        :params qs: A query string?
        :return DeclarativeMeta: an object
        """
        logging.debug("view_kwargs: %s, qs: %s", view_kwargs, qs)

        # analytics.write()
        # analytics.identify("anonymous", {"name": "Michael Bolton", "email": "mbolton@example.com", "created_at": datetime.now()})

        self.before_get_object(view_kwargs)

        record_id = view_kwargs["id"]
        logging.info("Looking up record for ID '%s'...", record_id)
        repo = self.repos[self.type]
        logging.debug("repo: %s", repo)
        try:
            record = repo.get(record_id)
            logging.debug("record: %s", record)
            if record is None:
                raise ObjectNotFound(f'No {self.type} record found for ID {view_kwargs["id"]}')
        except:
            raise ObjectNotFound(f'No {self.type} record found for ID {view_kwargs["id"]}')

        record = self.after_get_object(record, view_kwargs)
        logging.debug("record: %s", record)

        obj = self.model_info[self.type]["model"](**record)
        logging.debug("obj: %s", obj)

        return obj

    def get_collection(self, qs, view_kwargs, filters=None):
        """Retrieve a collection of objects
        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        :param dict filters: A dictionary of key/value filters to apply to the eventual query (ignored since it usually contains nothing)
        :return tuple: the number of objects and the list of objects
        """
        logging.debug("qs: %s, view_kwargs: %s, filters: %s", qs, view_kwargs, filters)
        logging.debug("querystring: %s", qs.querystring)
        logging.debug(
            "fields: %s, sorting: %s, include: %s, pagination: %s, filters: %s", qs.fields, qs.sorting, qs.include, qs.pagination, qs.filters
        )

        self.before_get_collection(qs, view_kwargs)

        query = self.query(qs, view_kwargs)
        query = self.paginate_query(query, qs.pagination)

        repo = self.repos[self.type]
        logging.debug("repo: %s", repo)
        objs = repo.query(query)
        logging.debug("objs: %s", objs)

        collection = self.after_get_collection(objs, qs, view_kwargs)

        return len(collection), collection

    def update_object(self, obj, data, view_kwargs):
        """Update an object
        :param DeclarativeMeta obj: an object
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if object have changed else False
        """
        logging.debug("obj: %s, data: %s, view_kwargs: %s", obj, data, view_kwargs)

        self.before_update_object(obj, data, view_kwargs)

        record_id = view_kwargs["id"]
        repo = self.repos[self.type]
        logging.debug("repo: %s", repo)
        try:
            updated_record = repo.update(record_id, data)
            logging.debug("updated_record: %s", updated_record)
        except:
            raise ObjectNotFound(f'Unable to delete {self.type} record for ID {view_kwargs["id"]}')

        self.after_update_object(updated_record, data, view_kwargs)

        return True

    def delete_object(self, obj, view_kwargs):
        """Delete an item through the data layer
        :param DeclarativeMeta obj: an object
        :param dict view_kwargs: kwargs from the resource view
        """
        logging.debug("obj: %s, view_kwargs: %s", obj, view_kwargs)

        self.before_delete_object(obj, view_kwargs)

        record_id = view_kwargs["id"]
        repo = self.repos[self.type]
        logging.debug("repo: %s", repo)
        try:
            is_deleted = repo.delete(record_id)
            logging.debug("is_deleted: %s", is_deleted)
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
        logging.debug(
            "json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
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

    def get_relationship(self, relationship_field, related_type, related_id_field, view_kwargs):
        """Get information about a relationship
        :param str relationship_field: the model attribute used for relationship
        :param str related_type: the related resource type
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the object and related object(s)
        """
        logging.debug(
            "relationship_field: %s, related_type: %s, related_id_field: %s, view_kwargs: %s",
            relationship_field,
            related_type,
            related_id_field,
            view_kwargs,
        )

        self.before_get_relationship(relationship_field, related_type, related_id_field, view_kwargs)

        # TODO

        self.after_get_relationship(obj, related_objects, relationship_field, related_type, related_id_field, view_kwargs)

        if isinstance(related_objects, InstrumentedList):
            return obj, [{"type": related_type, "id": getattr(obj_, related_id_field)} for obj_ in related_objects]
        else:
            return obj, {"type": related_type, "id": getattr(related_objects, related_id_field)}

    def update_relationship(self, json_data, relationship_field, related_id_field, view_kwargs):
        """Update a relationship
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if relationship have changed else False
        """
        logging.debug(
            "json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
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
        logging.debug(
            "json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
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
        logging.debug("qs: %s, view_kwargs: %s", qs, view_kwargs)

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
        logging.debug("query: %s, paginate_info: %s", query, paginate_info)

        if int(paginate_info.get("size", 1)) == 0:
            return query

        page_size = int(paginate_info.get("size", 0)) or current_app.config["PAGE_SIZE"]
        query.limit = page_size
        if paginate_info.get("number"):
            query.skip = (int(paginate_info["number"]) - 1) * page_size

        return query

    def _convert_properties(self, obj):
        """Convert some property values of an object, such as identifiers and date fields.

        :param obj: The object whose values should be converted.
        :return: The updated object.
        """
        logging.debug("obj: %s", obj)

        date_properties = ["created_at", "updated_at", "deleted_at"]
        id_properties = ["_id", "id"]
        for p in date_properties + id_properties:
            logging.debug("p (%s): %s", type(p), p)

            try:
                property_value = obj.get(p) or getattr(obj, p)
            except:
                logging.debug("could not get property value '%s'; skipping", p)
                continue

            logging.debug("property_value: %s", property_value)
            if property_value is None:
                continue

            logging.debug("initializing new_property_value with current value")
            new_property_value = property_value

            if p in date_properties:
                logging.debug("converting date property: %s, value: %s", p, property_value)
                new_property_value = to_datetime(property_value)
            elif p in id_properties:
                logging.debug("converting ID property: %s, value: %s", p, property_value)
                if isinstance(property_value, dict):
                    logging.debug("converting dictionary with possible $oid key")
                    new_property_value = property_value["$oid"]
                else:
                    logging.debug("coercing property value into string from %s", type(property_value))
                    new_property_value = str(property_value)

                logging.debug("new_property_value: %s", new_property_value)
                if p == "_id":
                    logging.debug("deleting old value with key '%s'", p)
                    del obj[p]
                    logging.debug("changing key of ID value '%s'", p)
                    p = "id"

            if isinstance(obj, dict):
                logging.debug("setting new dictionary value '%s' in dict %s: %s", p, obj, new_property_value)
                obj[p] = new_property_value
            else:
                logging.debug("setting new attribute value '%s' in object %s: %s", p, obj, new_property_value)
                setattr(obj, p, new_property_value)

        logging.debug("converted object: %s", obj)
        return obj

    def _populate_object(self, obj, properties: dict):
        """Populate an object's properties with sub-objects, where appropriate.

        :param obj: The object to populate.
        :param dict properties: A dictionary of the properties to populate. The key is the name of the property,
            the value is the property's type.
        :return: The populated object.
        """
        logging.debug("obj: %s, properties: %s", obj, properties)

        for property_name, property_type in properties.items():
            logging.debug("property_name: %s, property_type: %s", property_name, property_type)
            if not hasattr(obj, property_name) and not obj.get(property_name):
                continue
            property_value = obj.get(property_name) or getattr(obj, property_name)
            logging.debug("property_value: %s", property_value)
            if property_value is None:
                continue
            if isinstance(property_value, str):
                logging.debug("property_value is a string")

                new_property_value = self.repos[property_type].get(property_value)
                # logging.info("new_value: %s", new_value)
                logging.debug("new_property_value: %s", new_property_value)

                setattr(obj, property_name, new_property_value)

            if isinstance(property_value, list):
                logging.debug("property_value is a list")

                new_property_value = []
                for list_value in property_value:
                    logging.debug("list_value: %s", list_value)
                    if isinstance(list_value, dict) and list_value.get("$oid"):
                        value = list_value["$oid"]
                        new_property_value.append({"id": value})
                    else:
                        new_property_value.append(list_value)
                    # new_obj = self.repos[property_type].get(value)
                    # logging.debug("new_obj: %s", new_obj)
                    # new_value = json.loads(new_obj.to_json())
                    # logging.debug("new_value: %s", new_value)
                logging.debug("new_property_value: %s", new_property_value)

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
        logging.debug("data: %s, view_kwargs: %s", data, view_kwargs)

        if hasattr(data, 'id'):
            delattr(data, "id")
        if hasattr(data, 'deleted_at'):
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
        logging.debug("%s, data: %s, view_kwargs: %s", obj, data, view_kwargs)

    def before_get_object(self, view_kwargs):
        """Make work before to retrieve an object
        :param dict view_kwargs: kwargs from the resource view
        """
        logging.debug("view_kwargs: %s", view_kwargs)

    def after_get_object(self, obj, view_kwargs):
        """Work after fetching an object, including fetching child objects
        :param obj: an object from data layer
        :param dict view_kwargs: kwargs from the resource view
        """
        logging.debug("obj: %s, view_kwargs: %s", obj, view_kwargs)

        this_model = self.model_info[self.type]
        logging.debug("this_model: %s", this_model)
        properties = this_model.get("properties", {})
        logging.debug("properties: %s", properties)

        data = json.loads(obj.to_json())
        logging.debug("data: %s", data)
        converted_data = self._convert_properties(data)
        logging.debug("converted_data: %s", converted_data)
        obj = self._populate_object(converted_data, properties)
        logging.debug("obj: %s", obj)

        return obj

    def before_get_collection(self, qs, view_kwargs):
        """Make work before to retrieve a collection of objects
        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        """
        logging.debug("qs: %s, view_kwargs: %s", qs, view_kwargs)

    def after_get_collection(self, collection, qs, view_kwargs):
        """Make work after to retrieve a collection of objects
        :param iterable collection: the collection of objects
        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        """
        logging.debug("collection: %s, qs: %s, view_kwargs: %s", collection, qs, view_kwargs)

        this_model = self.model_info[self.type]
        logging.debug("this_model: %s", this_model)
        properties = this_model.get("properties", {})
        logging.debug("properties: %s", properties)

        updated_collection = []
        for obj in collection:
            logging.debug("obj: %s", obj)
            data = json.loads(obj.to_json())
            logging.debug("data: %s", data)
            converted_data = self._convert_properties(data)
            logging.debug("converted_data: %s", converted_data)
            obj = self._populate_object(converted_data, properties)
            logging.debug("obj: %s", obj)
            # logging.debug("obj: %s", obj)
            # self._populate_object(obj, properties)
            updated_collection.append(obj)

        return updated_collection

    def before_update_object(self, obj, data, view_kwargs):
        """Make checks or provide additional data before update object
        :param obj: an object from data layer
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        logging.debug("obj: %s, data: %s, view_kwargs: %s", obj, data, view_kwargs)

    def after_update_object(self, obj, data, view_kwargs):
        """Make work after update object
        :param obj: an object from data layer
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        logging.debug("obj: %s, data: %s, view_kwargs: %s", obj, data, view_kwargs)

    def before_delete_object(self, obj, view_kwargs):
        """Make checks before delete object
        :param obj: an object from data layer
        :param dict view_kwargs: kwargs from the resource view
        """
        logging.debug("obj: %s, view_kwargs: %s", obj, view_kwargs)

    def after_delete_object(self, obj, view_kwargs):
        """Make work after delete object
        :param obj: an object from data layer
        :param dict view_kwargs: kwargs from the resource view
        """
        logging.debug("obj: %s, view_kwargs: %s", obj, view_kwargs)

    def before_create_relationship(self, json_data, relationship_field, related_id_field, view_kwargs):
        """Make work before to create a relationship
        :param dict json_data: the request params
        :param str relationship_field: the model attribute used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if relationship have changed else False
        """
        logging.debug("relationship_field: %s, related_id_field: %s, view_kwargs: %s", relationship_field, related_id_field, view_kwargs)

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
        logging.debug(
            "obj: %s, update: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            obj,
            updated,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )

    def before_get_relationship(self, relationship_field, related_type, related_id_field, view_kwargs):
        """Make work before to get information about a relationship
        :param str relationship_field: the model attribute used for relationship
        :param str related_type: the related resource type
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the object and related object(s)
        """
        logging.debug(
            "relationship_field: %s, related_type: %s, related_id_field: %s, view_kwargs: %s",
            relationship_field,
            related_type,
            related_id_field,
            view_kwargs,
        )

    def after_get_relationship(self, obj, related_objects, relationship_field, related_type, related_id_field, view_kwargs):
        """Make work after to get information about a relationship
        :param obj: an object from data layer
        :param iterable related_objects: related objects of the object
        :param str relationship_field: the model attribute used for relationship
        :param str related_type: the related resource type
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the object and related object(s)
        """
        logging.debug(
            "obj: %s, relationship_field: %s, related_type: %s, related_id_field: %s, view_kwargs: %s",
            obj,
            relationship_field,
            related_type,
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
        logging.debug(
            "json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
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
        logging.debug(
            "obj: %s, update: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
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
        logging.debug(
            "json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
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
        logging.debug(
            "obj: %s, update: %s, json_data: %s, relationship_field: %s, related_id_field: %s, view_kwargs: %s",
            obj,
            updated,
            json_data,
            relationship_field,
            related_id_field,
            view_kwargs,
        )
