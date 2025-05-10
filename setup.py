"""
Setup script for the DomainSale package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="domainsale",
    version="0.1.0",
    author="DomainSaleGPT",
    author_email="info@example.com",
    description="A secure library for discovering and displaying 'for-sale' status of internet domains",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/domainsale",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Security",
    ],
    python_requires=">=3.7",
    install_requires=[
        "dnspython>=2.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "domainsale=domainsale.cli:main",
        ],
    },
)
