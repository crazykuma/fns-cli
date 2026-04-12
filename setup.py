from setuptools import setup, find_packages

setup(
    name="fns-cli",
    version="0.5.0",
    author="crazykuma",
    description="CLI tool for Fast Note Sync (Obsidian)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/crazykuma/fns-cli",
    py_modules=["fns"],
    python_requires=">=3.6",
    install_requires=[
        "click>=8.1",
    ],
    entry_points={
        "console_scripts": [
            "fns=fns:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
