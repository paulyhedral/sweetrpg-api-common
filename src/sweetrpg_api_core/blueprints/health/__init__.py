# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""health.py
Health endpoints.
"""

from flask import Blueprint, current_app, jsonify
from werkzeug.exceptions import HTTPException
import json
import os
from sweetrpg_api_core import constants
from sweetrpg_api_core.utils import SafeEncoder


blueprint = Blueprint("health", __name__, url_prefix="/health")

_health_check_service_hooks = {}


def register_health_check_service_hook(name: str, callable) -> None:
    """Add a callable service hook for the health check endpoint.

    :param name: The name of the hook.
    :param callable: A callable that will return a JSON-encodable result. If this is `None`,
        the hook will be deregistered.
    """
    if callable is None:
        del _health_check_service_hooks[name]
    else:
        _health_check_service_hooks[name] = callable


@blueprint.route("/status")
def health_check():
    r = {'services': {}, 'environment': {}}
    build_info_path = os.environ.get(constants.BUILD_INFO_PATH)
    if build_info_path:
        with open(build_info_path, "r") as bi:
            build_info = json.load(bi)
            r["build"] = build_info

    for k, v in _health_check_service_hooks.items():
        try:
            result = v()
            r['services'][k] = result
        except:
            r['services'][k] = 'Unknown'

    words = ['secret', 'pass', 'key', 'sentry_dsn', '_pw']
    for k, v in os.environ.items():
        for word in words:
            if word in k.lower():
                v = "***"
                break
        r['environment'][k] = v

    j = json.dumps(r, cls=SafeEncoder)

    return json.loads(j)


@blueprint.route("/ping")
def ping():
    return "pong"
