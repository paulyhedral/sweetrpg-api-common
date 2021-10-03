# -*- coding: utf-8 -*-
__author__ = "Paul Schifferer <dm@sweetrpg.com>"
"""
auth.py
- Authentication and authorization endpoints.
"""


from flask import Blueprint, current_app, jsonify
from werkzeug.exceptions import HTTPException
import json
from sweetrpg_library_api.application.blueprints import error_page


blueprint = Blueprint("health", __name__, url_prefix='/health')


@blueprint.errorhandler(Exception)
def handle_error(ex):
    code = (ex.code if isinstance(ex, HTTPException) else 500)
    return error_page(str(ex), code)


@blueprint.route('/status')
def health_check():
    with open(f'/{current_app.static_folder}/build-info.json', 'r') as bi:
        build_info = json.load(bi)
        return {
            'build': build_info,
            'services': {}
        }


@blueprint.route('/ping')
def ping():
    return "pong"
