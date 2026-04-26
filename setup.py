from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="askdb",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "transformers>=4.30.0",
        "sentencepiece",
        "torch",
        "fuzzywuzzy",
        "python-Levenshtein",
    ],
    extras_require={
        "postgresql": ["psycopg2-binary"],
        "mysql": ["pymysql"],
        "mongodb": ["pymongo"],
        "all": ["psycopg2-binary", "pymysql", "pymongo"],
    },
    author="Bhanu Prasad Thota",
    author_email="bhanuprasadt27@gmail.com",
    description="Convert natural language queries to SQL — no SQL knowledge required.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bhanuprasadthota/AskDB",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="sql nlp text-to-sql natural-language database query",
)
