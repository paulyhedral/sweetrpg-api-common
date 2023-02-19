from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="sweetrpg-api-core",
    install_requires=[
        "Flask<3.0",
        "sweetrpg-db",
        "sweetrpg-model-core",
        "mongoengine==0.26.0",
        "Flask-REST-JSONAPI",
    ],
    extras_require={},
)
