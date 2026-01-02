"""Service layer with caching, request coalescing, and rate limiting."""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict
from cachetools import TTLCache
from .ytdlp_wrapper import YtDlpWrapper
from .config import settings

logger = logging.getLogger(__name__)


class VideoService:
    """
    High-performance service layer with intelligent caching and request coalescing.
    
    Features:
    - TTL cache to prevent redundant yt-dlp calls
    - Request coalescing: multiple requests for same URL share single execution
    - Per-IP rate limiting
    - Memory-efficient design
    """
    
    def __init__(self):
        """Initialize service with cache and yt-dlp wrapper."""
        # TTL cache: auto-expires entries after cache_ttl_seconds
        self._cache = TTLCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_ttl_seconds
        )
        
        # Separate cache for formats (longer TTL since formats rarely change)
        self._formats_cache = TTLCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_ttl_seconds * 2  # 2x longer cache for formats
        )
        
        # Request coalescing: track in-flight requests by URL
        self._in_flight: Dict[str, asyncio.Future] = {}
        self._in_flight_lock = asyncio.Lock()
        
        # Rate limiting: track requests per IP
        self._rate_limiter: Dict[str, list] = defaultdict(list)
        self._rate_limit_lock = asyncio.Lock()
        
        # yt-dlp wrapper
        self._ytdlp = YtDlpWrapper()
        
        logger.info("VideoService initialized with caching and request coalescing")
    
    async def get_available_formats(self, url: str, client_ip: str = "unknown") -> Dict[str, Any]:
        """
        Get all available formats for a video with caching and request coalescing.
        
        Args:
            url: Video URL
            client_ip: Client IP for rate limiting
            
        Returns:
            Dictionary containing video metadata and available formats
            
        Raises:
            ValueError: If rate limit exceeded
            RuntimeError: If video extraction fails
        """
        # Check rate limit
        await self._check_rate_limit(client_ip)
        
        # Generate cache key
        cache_key = f"formats:{url}"
        
        # Check cache first
        if cache_key in self._formats_cache:
            logger.info(f"Formats cache hit for URL: {url[:50]}...")
            return self._formats_cache[cache_key]
        
        # Check if request is already in-flight (request coalescing)
        async with self._in_flight_lock:
            if cache_key in self._in_flight:
                logger.info(f"Request coalescing: waiting for in-flight formats request for {url[:50]}...")
                future = self._in_flight[cache_key]
            else:
                # Create new future for this request
                future = asyncio.Future()
                self._in_flight[cache_key] = future
        
        # If we created the future, execute the request
        if not future.done():
            try:
                result = await self._ytdlp.get_formats(url)
                
                # Sort formats by resolution (highest first)
                formats = result.get('formats', [])
                
                def sort_key(fmt):
                    """Sort key: prioritize by resolution (height), then filesize."""
                    height = fmt.get('height', 0) or 0
                    filesize = fmt.get('filesize', 0) or 0
                    # Return negative values for descending sort
                    return (-height, -filesize)
                
                formats.sort(key=sort_key)
                result['formats'] = formats
                
                # Cache the result
                self._formats_cache[cache_key] = result
                
                # Complete the future for all waiting requests (only if not already done)
                if not future.done():
                    future.set_result(result)
                
                return result
            except Exception as e:
                # Propagate error to all waiting requests (only if not already done)
                if not future.done():
                    future.set_exception(e)
                raise
            finally:
                # Clean up in-flight tracking
                async with self._in_flight_lock:
                    self._in_flight.pop(cache_key, None)
        else:
            # Wait for the in-flight request to complete
            return await future
    
    async def get_video_info(self, url: str, format_id: Optional[str] = None, client_ip: str = "unknown", ensure_audio: bool = True) -> Dict[str, Any]:
        """
        Get video information with caching and request coalescing.
        
        Args:
            url: Video URL
            format_id: Optional specific format
            client_ip: Client IP for rate limiting
            
        Returns:
            Video metadata dictionary
            
        Raises:
            ValueError: If rate limit exceeded
            RuntimeError: If video extraction fails
        """
        # Check rate limit
        await self._check_rate_limit(client_ip)
        
        # Generate cache key
        cache_key = f"{url}:{format_id or 'default'}"
        
        # Check cache first
        if cache_key in self._cache:
            logger.info(f"Cache hit for URL: {url[:50]}...")
            return self._cache[cache_key]
        
        # Check if request is already in-flight (request coalescing)
        async with self._in_flight_lock:
            if cache_key in self._in_flight:
                logger.info(f"Request coalescing: waiting for in-flight request for {url[:50]}...")
                future = self._in_flight[cache_key]
            else:
                # Create new future for this request
                future = asyncio.Future()
                self._in_flight[cache_key] = future
        
        # If we created the future, execute the request
        if not future.done():
            try:
                # For downloads, always ensure audio is merged (fixes video-only "combined" formats)
                result = await self._ytdlp.extract_info(url, format_id, ensure_audio=ensure_audio)
                
                # Cache the result
                self._cache[cache_key] = result
                
                # Complete the future for all waiting requests
                future.set_result(result)
                
                return result
            except Exception as e:
                # Propagate error to all waiting requests
                future.set_exception(e)
                raise
            finally:
                # Clean up in-flight tracking
                async with self._in_flight_lock:
                    self._in_flight.pop(cache_key, None)
        else:
            # Wait for the in-flight request to complete
            return await future
    
    async def _check_rate_limit(self, client_ip: str) -> None:
        """
        Check and enforce rate limiting per IP address.
        
        Args:
            client_ip: Client IP address
            
        Raises:
            ValueError: If rate limit exceeded
        """
        async with self._rate_limit_lock:
            now = time.time()
            minute_ago = now - 60
            
            # Clean old entries
            self._rate_limiter[client_ip] = [
                timestamp for timestamp in self._rate_limiter[client_ip]
                if timestamp > minute_ago
            ]
            
            # Check limit
            if len(self._rate_limiter[client_ip]) >= settings.rate_limit_per_minute:
                raise ValueError(f"Rate limit exceeded: {settings.rate_limit_per_minute} requests per minute")
            
            # Add current request
            self._rate_limiter[client_ip].append(now)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            'cache_size': len(self._cache),
            'cache_max_size': self._cache.maxsize,
            'formats_cache_size': len(self._formats_cache),
            'in_flight_requests': len(self._in_flight),
            'active_ytdlp_processes': self._ytdlp.active_processes,
        }
    
    def clear_cache(self) -> None:
        """Clear the cache (useful for testing or maintenance)."""
        self._cache.clear()
        self._formats_cache.clear()
        logger.info("Cache cleared")

