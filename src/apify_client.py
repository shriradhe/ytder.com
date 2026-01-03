"""Apify API client for YouTube video extraction (fallback when yt-dlp fails)."""
import asyncio
import logging
import json
from typing import Dict, Any, Optional
import httpx
from .config import settings

logger = logging.getLogger(__name__)


class ApifyClient:
    """Client for Apify API to extract YouTube video information."""
    
    BASE_URL = "https://api.apify.com/v2"
    
    def __init__(self):
        """Initialize Apify client."""
        self.api_token = settings.apify_api_token
        self.actor_id = settings.apify_actor_id
        self.timeout = settings.apify_timeout_seconds
        self.enabled = settings.apify_enabled and self.api_token is not None
        
        if self.enabled:
            logger.info(f"Apify client enabled with actor: {self.actor_id}")
        elif settings.apify_enabled and not self.api_token:
            logger.warning("Apify is enabled but APIFY_API_TOKEN is not set")
        else:
            logger.info("Apify client disabled (set APIFY_ENABLED=true and APIFY_API_TOKEN to enable)")
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get YouTube video information using Apify API.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dictionary containing video metadata and formats
            
        Raises:
            RuntimeError: If Apify API call fails
        """
        if not self.enabled:
            raise RuntimeError("Apify client is not enabled or API token is missing")
        
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
        
        logger.info(f"Using Apify API to extract video info for: {video_id}")
        
        # Start actor run
        run_id = await self._start_actor_run(video_id)
        
        # Wait for run to complete and get results
        results = await self._wait_for_run_completion(run_id)
        
        # Process and return results
        return self._process_results(results, url)
    
    async def _start_actor_run(self, video_id: str) -> str:
        """Start an Apify actor run."""
        # Apify API uses ~ instead of / in actor IDs for the URL
        actor_id_url = self.actor_id.replace("/", "~")
        url = f"{self.BASE_URL}/acts/{actor_id_url}/runs"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare input based on actor type
        if "youtube-scraper" in self.actor_id.lower():
            # For apify/youtube-scraper
            payload = {
                "startUrls": [{"url": f"https://www.youtube.com/watch?v={video_id}"}],
                "maxVideos": 1
            }
        elif "yt-downloader" in self.actor_id.lower():
            # For bluepenguins455/yt-downloader
            payload = {
                "videoUrls": [f"https://www.youtube.com/watch?v={video_id}"],
                "quality": "best"
            }
        else:
            # Generic payload
            payload = {
                "videoUrl": f"https://www.youtube.com/watch?v={video_id}",
                "videoId": video_id
            }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                run_id = data["data"]["id"]
                logger.info(f"Apify actor run started: {run_id}")
                return run_id
            except httpx.HTTPStatusError as e:
                error_msg = f"Apify API error: {e.response.status_code} - {e.response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            except Exception as e:
                error_msg = f"Failed to start Apify actor run: {str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
    
    async def _wait_for_run_completion(self, run_id: str) -> Dict[str, Any]:
        """Wait for Apify actor run to complete and return results."""
        status_url = f"{self.BASE_URL}/actor-runs/{run_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        
        max_wait_time = self.timeout
        check_interval = 2  # Check every 2 seconds
        elapsed = 0
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while elapsed < max_wait_time:
                try:
                    # Check run status
                    response = await client.get(status_url, headers=headers)
                    response.raise_for_status()
                    run_data = response.json()["data"]
                    status = run_data["status"]
                    
                    if status == "SUCCEEDED":
                        # Get results from dataset
                        results_url = f"{status_url}/dataset/items"
                        results_response = await client.get(results_url, headers=headers)
                        results_response.raise_for_status()
                        results = results_response.json()["data"]
                        logger.info(f"Apify actor run completed successfully: {run_id}")
                        return results[0] if results else {}
                    
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        error_msg = f"Apify actor run {status.lower()}: {run_data.get('statusMessage', 'Unknown error')}"
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)
                    
                    # Still running, wait and check again
                    await asyncio.sleep(check_interval)
                    elapsed += check_interval
                    
                except httpx.HTTPStatusError as e:
                    error_msg = f"Apify API error checking run status: {e.response.status_code}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                except Exception as e:
                    if "SUCCEEDED" not in str(e) and "FAILED" not in str(e):
                        error_msg = f"Error checking Apify run status: {str(e)}"
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)
            
            # Timeout
            raise RuntimeError(f"Apify actor run timed out after {max_wait_time}s")
    
    def _process_results(self, results: Dict[str, Any], original_url: str) -> Dict[str, Any]:
        """
        Process Apify results into our standard format.
        
        Args:
            results: Raw results from Apify API
            original_url: Original YouTube URL
            
        Returns:
            Processed video metadata in our standard format
        """
        # Extract video information (format depends on actor)
        title = (
            results.get("title") or 
            results.get("name") or 
            results.get("videoTitle") or 
            "Unknown"
        )
        
        thumbnail = (
            results.get("thumbnail") or 
            results.get("thumbnailUrl") or 
            results.get("thumbnail_url") or
            results.get("thumbnails", [{}])[0].get("url") if isinstance(results.get("thumbnails"), list) else None
        )
        
        duration = (
            results.get("duration") or 
            results.get("durationSeconds") or
            results.get("lengthSeconds")
        )
        
        uploader = (
            results.get("uploader") or 
            results.get("channel") or 
            results.get("channelName") or
            results.get("author")
        )
        
        view_count = (
            results.get("viewCount") or 
            results.get("views") or
            results.get("view_count")
        )
        
        # Extract formats/qualities
        formats = []
        
        # Try to extract format information
        if "formats" in results:
            # Direct formats array
            formats_data = results["formats"]
        elif "videoFormats" in results:
            formats_data = results["videoFormats"]
        elif "downloadLinks" in results:
            formats_data = results["downloadLinks"]
        else:
            # Try to construct from available data
            formats_data = []
            if results.get("videoUrl") or results.get("downloadUrl"):
                formats_data.append({
                    "url": results.get("videoUrl") or results.get("downloadUrl"),
                    "quality": results.get("quality", "best"),
                    "format": "combined"
                })
        
        # Process formats
        for fmt in formats_data if isinstance(formats_data, list) else []:
            format_info = {
                "format_id": fmt.get("itag") or fmt.get("formatId") or "unknown",
                "ext": fmt.get("ext") or fmt.get("extension") or "mp4",
                "quality": fmt.get("quality") or fmt.get("qualityLabel") or "unknown",
                "format_note": fmt.get("formatNote") or fmt.get("qualityLabel"),
                "filesize": fmt.get("filesize") or fmt.get("contentLength"),
                "vcodec": fmt.get("vcodec") or "none",
                "acodec": fmt.get("acodec") or "none",
                "format_type": "combined" if (fmt.get("vcodec") and fmt.get("acodec")) else ("video" if fmt.get("vcodec") else "audio"),
            }
            formats.append(format_info)
        
        # If no formats found, create a default one
        if not formats:
            formats.append({
                "format_id": "best",
                "ext": "mp4",
                "quality": "best",
                "format_note": "Best available",
                "filesize": None,
                "vcodec": "unknown",
                "acodec": "unknown",
                "format_type": "combined",
            })
        
        return {
            "title": title,
            "thumbnail": thumbnail,
            "duration": duration,
            "uploader": uploader,
            "view_count": view_count,
            "formats": formats,
            "url": original_url,  # Use original URL
            "_source": "apify"  # Mark as from Apify
        }

