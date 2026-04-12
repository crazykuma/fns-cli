from setuptools import setup, find_packages

setup(
    name="fns-cli",
    version="0.1.0",
    author="Peter Yan",
    description="CLI tool for Fast Note Sync (Obsidian)",
    py_modules=["fns"],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "fns=fns:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
