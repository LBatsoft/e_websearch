from setuptools import setup, find_packages

setup(
    name="e_websearch",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "loguru",
        "pytest",
        "pytest-asyncio"
    ]
)
