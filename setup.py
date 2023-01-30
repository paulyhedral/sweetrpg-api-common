from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="sweetrpg-api-core",
    install_requires=[
        "Flask<3.0",
        "sweetrpg-db",
        "sweetrpg-model-core",
        "mongoengine @ git+https://github.com/MongoEngine/mongoengine.git",
        "Flask-REST-JSONAPI",
    ],
    extras_require={},
)
