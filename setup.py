"""
Setup script for the MonitorPy package.
"""

from setuptools import setup, find_packages

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="monitorpy",
    version="0.0.1",
    author="Bonzo",
    author_email="bonzo@konjscina.com",
    description="A plugin-based website and service monitoring system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/monitorpy",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "monitorpy=monitorpy.cli:main",
        ],
    },
)
