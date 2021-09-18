from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="SweetRPG API Common",
    install_requires=["Flask>=2.0",
"sweetrpg-common @ git+https://github.com/sweetrpg/common.git@develop"
],
    extras_require={},
)
