from setuptools import setup, find_packages

setup(
    name="whs2utils",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "click",
    ],
    entry_points={
        "console_scripts": [
            "whs2utils=whs2utils.cli:cli",
        ],
    },
)
