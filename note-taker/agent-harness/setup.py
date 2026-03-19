from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-note-taker",
    version="1.0.0",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=["click>=8.0"],
    entry_points={
        "console_scripts": [
            "cli-anything-note-taker=cli_anything.note_taker.note_taker_cli:main",
        ],
    },
)
