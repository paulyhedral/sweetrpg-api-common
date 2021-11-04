# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""
"""

from marshmallow_jsonapi.flask import Schema, Relationship
from marshmallow_jsonapi import fields
from marshmallow import post_load
import logging


class BaseAPISchema(Schema):
    """A base schema for API data."""

    id = fields.Str()  # as_string=True, dump_only=True)
    created_at = fields.DateTime()  # dump_only=True)
    created_by = fields.String()
    updated_at = fields.DateTime()  # dump_only=True)
    updated_by = fields.String()
    deleted_at = fields.DateTime()
    deleted_by = fields.String()
    document_meta = fields.DocumentMeta()
    resource_meta = fields.ResourceMeta()

    @post_load
    def make_object(self, data, **kwargs):
        logging.debug("data: %s, kwargs: %s", data, kwargs)
        return self.model_class(**data)
