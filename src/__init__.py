"""
Video Download Service - Source Package

A high-performance FastAPI-based backend service for video metadata extraction
and download link generation.

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Video Downloader Team"

# Package exports
from .config import settings
from .database import get_db, init_db

__all__ = [
    "settings",
    "get_db",
    "init_db",
    "__version__",
]
