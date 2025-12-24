"""
DeepForge Setup
Installation script for DeepForge.
"""

from setuptools import setup, find_packages
from pathlib import Path

readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="deepforge",
    version="0.1.0",
    description="Autonomous AI-powered software development platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DeepForge Team",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0",
        "pyyaml>=6.0",
        "click>=8.0",
        "gitpython>=3.1",
        "psutil>=5.9",
        "requests>=2.31.0",
        "fastapi>=0.100",
        "uvicorn>=0.23",
        "pytest>=7.4",
        "pytest-asyncio>=0.21",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4",
            "pytest-asyncio>=0.21",
        ],
        "ml": [
            "transformers>=4.30",
            "torch>=2.0",
            "llama-cpp-python>=0.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "deepforge=interface.cli.deepforge:cli",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

