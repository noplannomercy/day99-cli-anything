from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-mini-crm",
    version="1.0.0",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=["click>=8.0", "psycopg2-binary"],
    entry_points={
        "console_scripts": [
            "cli-anything-mini-crm=cli_anything.mini_crm.mini_crm_cli:main",
        ],
    },
)
