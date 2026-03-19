from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-unit-converter",
    version="1.0.0",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=["click>=8.0"],
    entry_points={
        "console_scripts": [
            "cli-anything-unit-converter=cli_anything.unit_converter.unit_converter_cli:main",
        ],
    },
)
