from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="sweetrpg-api-core",
    install_requires=[
        "Flask~=2.0",
        "sweetrpg-db",
        "sweetrpg-model-core",
        "mongoengine~=0.27",
        "Flask-REST-JSONAPI~=0.31",
    ],
    extras_require={},
)
