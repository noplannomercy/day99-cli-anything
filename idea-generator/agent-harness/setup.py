from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-idea-generator",
    version="1.0.0",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=["click>=8.0"],
    entry_points={
        "console_scripts": [
            "cli-anything-idea-generator=cli_anything.idea_generator.idea_generator_cli:main",
        ],
    },
)
