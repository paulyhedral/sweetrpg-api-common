from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="sweetrpg-api-core",
    install_requires=[
        "Flask==2.0.2",
        "sweetrpg-db",
        "sweetrpg-model-core",
        "mongoengine",
        "Flask-REST-JSONAPI",
    ],
    extras_require={},
)
