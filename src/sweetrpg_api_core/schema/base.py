# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""
"""

from marshmallow_jsonapi.flask import Schema, Relationship
from marshmallow_jsonapi import fields
from marshmallow import post_load
import logging


class BaseAPISchema(Schema):
    """A base schema for APIs."""

    id = fields.Str()  # as_string=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    deleted_at = fields.DateTime()

    @post_load
    def make_object(self, data, **kwargs):
        logging.debug("data: %s, kwargs: %s", data, kwargs)
        return self.model_class(**data)
