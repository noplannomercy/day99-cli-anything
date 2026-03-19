from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-wikiflow",
    version="0.1.0",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=["click"],
    entry_points={
        "console_scripts": [
            "cli-anything-wikiflow=cli_anything.wikiflow.wikiflow_cli:cli",
        ]
    },
)
