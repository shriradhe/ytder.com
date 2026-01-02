"""Setup script for ytder-python-backend."""
# setuptools is a build dependency, not a runtime dependency
# It's typically pre-installed with Python or installed via pip
from setuptools import setup, find_packages  # type: ignore

# README.md is in root directory
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# setup() function from setuptools - this is the standard way to configure Python packages
# The red warning in IDE is normal - setuptools is a build-time dependency
setup(  # type: ignore[call-overload]
    name="ytder-python-backend",
    version="1.0.0",
    author="Video Downloader Team",
    description="High-performance FastAPI backend for video metadata extraction and download",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ytder-python-backend",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    # Note: Use 'python start.py' or 'uvicorn main:app' to run the application
    # Entry point removed - FastAPI apps are typically run via uvicorn
    include_package_data=True,
    zip_safe=False,
)

