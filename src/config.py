"""Configuration settings for the video download service."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with sensible defaults for production."""
    
    # Server settings
    # Use 0.0.0.0 for Render.com (allows external connections)
    # Use 127.0.0.1 for local development
    host: str = os.getenv("HOST", "0.0.0.0")
    # Render.com sets PORT environment variable automatically
    port: int = int(os.getenv("PORT", "8000"))
    
    # Concurrency settings
    max_concurrent_downloads: int = 10  # Max parallel yt-dlp processes
    max_queue_size: int = 100  # Max queued requests before rejection
    
    # Cache settings
    cache_ttl_seconds: int = 3600  # 1 hour cache for video metadata
    cache_max_size: int = 1000  # Max cached items
    
    # Rate limiting
    rate_limit_per_minute: int = 30  # Per IP address
    
    # Timeouts
    ytdlp_timeout_seconds: int = 60  # Max time for yt-dlp execution
    
    # yt-dlp settings
    ytdlp_format: str = "best"  # Video quality selector
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

