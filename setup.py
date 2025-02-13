#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 13:26:35 2025

@author: bhanuprasadthota
"""

from setuptools import setup, find_packages

setup(
    name="askdb",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["transformers", "sentencepiece"],
    author="Bhanu Prasad Thota",
    description="A self-hosted NLP-based SQL query engine",
    url="https://github.com/bhanuprasadthota/AskDB",
    license="MIT",
)
