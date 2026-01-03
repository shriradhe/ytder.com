"""Configuration settings for the video download service."""
import os
from typing import Optional
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
    
    # Proxy settings (for geo-blocking bypass)
    # Supports HTTP, HTTPS, SOCKS4, SOCKS5 proxies
    # Format: http://user:pass@host:port or socks5://host:port
    proxy: Optional[str] = os.getenv("PROXY", None)
    
    # Cookies settings (automatically used for all requests)
    # Path to cookies.txt file (Netscape format or JSON format)
    cookies_file: Optional[str] = os.getenv("COOKIES_FILE", os.getenv("YOUTUBE_COOKIES_FILE", None))
    
    # Apify API settings (fallback when yt-dlp fails)
    # Get API token from: https://console.apify.com/account/integrations
    apify_api_token: Optional[str] = os.getenv("APIFY_API_TOKEN", None)
    # Apify Actor ID for YouTube scraping (default: YouTube Scraper)
    # Popular actors: "apify/youtube-scraper", "bluepenguins455/yt-downloader"
    apify_actor_id: str = os.getenv("APIFY_ACTOR_ID", "apify/youtube-scraper")
    # Timeout for Apify API calls (in seconds)
    apify_timeout_seconds: int = int(os.getenv("APIFY_TIMEOUT_SECONDS", "120"))
    # Enable Apify as fallback (set to "true" to enable)
    apify_enabled: bool = os.getenv("APIFY_ENABLED", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

