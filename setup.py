from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="sweetrpg-api-core",
    install_requires=[
        "Flask>=2.0",
        "sweetrpg-db @ git+https://github.com/sweetrpg/db.git@develop",
        "mongoengine",
        "Flask-REST-JSONAPI",
    ],
    extras_require={},
)
