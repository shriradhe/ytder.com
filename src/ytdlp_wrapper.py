"""Async wrapper for yt-dlp with efficient subprocess handling."""
import asyncio
import json
import logging
import time
import os
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from .config import settings

logger = logging.getLogger(__name__)

# Import Apify client (optional fallback)
try:
    from .apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False
    ApifyClient = None


def _get_base_options() -> list:
    """
    Get base options that apply to all requests (proxy, cookies).
    
    Returns:
        List of command-line arguments for yt-dlp
    """
    options = []
    
    # Add proxy if configured (for geo-blocking bypass)
    if settings.proxy:
        options.extend(["--proxy", settings.proxy])
        logger.info(f"Using proxy: {settings.proxy[:50]}..." if len(settings.proxy) > 50 else f"Using proxy: {settings.proxy}")
    
    # Automatically use cookies file if configured
    if settings.cookies_file and os.path.exists(settings.cookies_file):
        options.extend(["--cookies", settings.cookies_file])
        logger.info(f"Using cookies from: {settings.cookies_file}")
    elif settings.cookies_file:
        logger.warning(f"Cookies file specified but not found: {settings.cookies_file}")
    
    return options


def _get_generic_options() -> list:
    """
    Get generic options for non-YouTube URLs (includes proxy, cookies, user-agent).
    
    Returns:
        List of command-line arguments for yt-dlp
    """
    options = _get_base_options()
    options.extend([
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ])
    return options


def _get_youtube_options(player_client: str = "ios") -> list:
    """
    Get YouTube-specific options to bypass bot detection.
    
    Args:
        player_client: Which player client to use ('ios', 'android', 'web', 'mweb')
                      iOS is often most reliable for bypassing bot detection
    
    Returns:
        List of command-line arguments for yt-dlp
    """
    # Start with base options (proxy, cookies)
    options = _get_base_options()
    
    # Add YouTube-specific headers
    options.extend([
        "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "--referer", "https://www.youtube.com/",
        "--add-header", "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "--add-header", "Accept-Language:en-US,en;q=0.9",
        "--add-header", "Accept-Encoding:gzip, deflate, br",
        "--add-header", "Sec-Fetch-Dest:document",
        "--add-header", "Sec-Fetch-Mode:navigate",
        "--add-header", "Sec-Fetch-Site:none",
        "--add-header", "Sec-Fetch-User:?1",
        "--add-header", "Upgrade-Insecure-Requests:1",
    ])
    
    # Add YouTube extractor args - try different player clients
    # iOS client is often most reliable for bypassing bot detection
    youtube_extractor_args = [
        f"player_client={player_client}",
        "player_skip=webpage",  # Skip webpage parsing, use API directly
    ]
    
    options.extend([
        "--extractor-args", f"youtube:{','.join(youtube_extractor_args)}"
    ])
    
    return options


class YtDlpWrapper:
    """Non-blocking yt-dlp wrapper using async subprocess."""
    
    def __init__(self):
        """Initialize the wrapper with a semaphore for concurrency control."""
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
        self._active_processes = 0
        
        # Initialize Apify client if available and enabled
        self._apify_client = None
        if APIFY_AVAILABLE and settings.apify_enabled:
            try:
                self._apify_client = ApifyClient()
                if self._apify_client.enabled:
                    logger.info("Apify fallback enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Apify client: {e}")
        
        # Log configuration
        logger.info(f"YtDlpWrapper initialized with max {settings.max_concurrent_downloads} concurrent processes")
        
        # Log yt-dlp version
        try:
            import subprocess
            result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"yt-dlp version: {version}")
            else:
                logger.warning("Could not determine yt-dlp version")
        except Exception as e:
            logger.warning(f"Could not check yt-dlp version: {e}")
        
        if settings.proxy:
            logger.info(f"Proxy enabled: {settings.proxy[:50]}..." if len(settings.proxy) > 50 else f"Proxy enabled: {settings.proxy}")
        if settings.cookies_file and os.path.exists(settings.cookies_file):
            logger.info(f"Cookies enabled: {settings.cookies_file}")
        elif settings.cookies_file:
            logger.warning(f"Cookies file specified but not found: {settings.cookies_file}")
    
    async def get_formats(self, url: str) -> Dict[str, Any]:
        """
        Get all available formats for a video without downloading.
        
        Args:
            url: Video URL to process
            
        Returns:
            Dictionary containing video metadata and all available formats
            
        Raises:
            RuntimeError: If yt-dlp execution fails
            asyncio.TimeoutError: If execution exceeds timeout
        """
        async with self._semaphore:
            self._active_processes += 1
            try:
                logger.info(f"Fetching formats for URL: {url[:50]}... (active: {self._active_processes})")
                
                # Build yt-dlp command to get all formats
                cmd = [
                    "yt-dlp",
                    "--dump-json",  # Output JSON metadata only
                    "--no-playlist",  # Single video only
                    "--no-warnings",
                    "--no-check-certificate",
                ]
                # For YouTube URLs, try multiple player clients to bypass bot detection
                is_youtube = "youtube.com" in url or "youtu.be" in url
                player_clients = ["ios", "android", "web", "mweb"] if is_youtube else [None]
                last_error = None
                
                for client in player_clients:
                    try:
                        cmd = [
                            "yt-dlp",
                            "--dump-json",
                            "--no-playlist",
                            "--no-warnings",
                            "--no-check-certificate",
                        ]
                        
                        if client:
                            cmd.extend(_get_youtube_options(player_client=client))
                            logger.info(f"Trying YouTube with player_client={client}")
                        else:
                            # For non-YouTube URLs, use generic options (includes proxy, cookies)
                            cmd.extend(_get_generic_options())
                        cmd.append(url)
                        
                        # Execute yt-dlp as async subprocess
                        process = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        
                        # Wait with timeout
                        try:
                            stdout, stderr = await asyncio.wait_for(
                                process.communicate(),
                                timeout=settings.ytdlp_timeout_seconds
                            )
                        except asyncio.TimeoutError:
                            process.kill()
                            await process.wait()
                            raise asyncio.TimeoutError(f"yt-dlp execution exceeded {settings.ytdlp_timeout_seconds}s timeout")
                        
                        # Check exit code
                        if process.returncode != 0:
                            error_msg = stderr.decode('utf-8', errors='ignore').strip()
                            # Check if it's a retryable error (bot detection or player response failure)
                            retryable_errors = [
                                "Sign in to confirm",
                                "bot",
                                "Failed to extract any player response",
                                "Unable to extract video data"
                            ]
                            should_retry = is_youtube and any(err.lower() in error_msg.lower() for err in retryable_errors)
                            
                            if should_retry:
                                logger.warning(f"Retryable error with player_client={client}: {error_msg[:100]}...")
                                last_error = error_msg
                                continue  # Try next client
                            else:
                                # Other error, don't retry
                                logger.error(f"yt-dlp failed with code {process.returncode}: {error_msg}")
                                raise RuntimeError(f"yt-dlp execution failed: {error_msg or 'Unknown error'}")
                        
                        # Success! Parse and return
                        output = stdout.decode('utf-8', errors='ignore')
                        metadata = json.loads(output)
                        logger.info(f"Successfully fetched {len(metadata.get('formats', []))} formats for: {metadata.get('title', 'Unknown')} (client={client or 'default'})")
                        return self._process_formats(metadata)
                        
                    except (RuntimeError, json.JSONDecodeError) as e:
                        error_str = str(e)
                        # If it's not a bot detection error, re-raise
                        if not is_youtube or ("Sign in to confirm" not in error_str and "bot" not in error_str.lower()):
                            raise
                        last_error = error_str
                        continue
                
                # All clients failed - try Apify as fallback
                if last_error:
                    logger.error(f"All player clients failed. Last error: {last_error}")
                    
                    # Try Apify as fallback if enabled and available
                    if self._apify_client and self._apify_client.enabled and is_youtube:
                        logger.info("Attempting Apify API as fallback...")
                        try:
                            apify_result = await self._apify_client.get_video_info(url)
                            logger.info("Successfully extracted video info using Apify API")
                            return self._process_formats(apify_result)
                        except Exception as apify_error:
                            logger.error(f"Apify fallback also failed: {str(apify_error)}")
                            # Continue to raise the original yt-dlp error
                    
                    raise RuntimeError(f"yt-dlp execution failed after trying all player clients: {last_error}")
                else:
                    raise RuntimeError("yt-dlp execution failed: Unknown error")
                
            finally:
                self._active_processes -= 1
    
    async def extract_info(self, url: str, format_id: Optional[str] = None, ensure_audio: bool = True) -> Dict[str, Any]:
        """
        Extract video metadata using yt-dlp without downloading the file.
        
        Args:
            url: Video URL to process
            format_id: Optional specific format ID
            ensure_audio: If True, always merge with best audio for video formats (default: True)
            
        Returns:
            Dictionary containing video metadata
            
        Raises:
            RuntimeError: If yt-dlp execution fails
            asyncio.TimeoutError: If execution exceeds timeout
        """
        async with self._semaphore:  # Limit concurrent yt-dlp processes
            self._active_processes += 1
            try:
                logger.info(f"Starting yt-dlp extraction for URL: {url[:50]}... (active: {self._active_processes})")
                
                # For downloads with ensure_audio, we need to actually download and merge the file
                # because --dump-json doesn't merge - it only gives metadata
                # ALWAYS merge when ensure_audio=True, regardless of format_id format
                temp_file_path = None
                if ensure_audio and format_id:
                    # Create temp file for merged download
                    temp_dir = tempfile.gettempdir()
                    timestamp = int(time.time() * 1000)  # Use milliseconds for uniqueness
                    temp_file_path = os.path.join(temp_dir, f"ytdlp_merge_{os.getpid()}_{timestamp}.%(ext)s")
                    
                    # Check if format_id already contains merge operators (e.g., "123+456")
                    if '+' in format_id:
                        # Format ID already specifies video+audio combination
                        # Ensure both parts are valid format IDs
                        parts = format_id.split('+')
                        if len(parts) == 2:
                            video_id, audio_id = parts
                            # Use explicit format selector - yt-dlp will merge automatically
                            # Don't add fallbacks as it might cause issues
                            format_selector = f"{video_id}+{audio_id}"
                            logger.info(f"Using combined format selector: {format_selector}")
                            
                            # Verify FFmpeg is available for merging
                            if not shutil.which('ffmpeg'):
                                logger.error("⚠️ FFmpeg is not installed or not in PATH!")
                                logger.error("   yt-dlp requires FFmpeg to merge video and audio streams.")
                                logger.error("   Install FFmpeg from: https://ffmpeg.org/download.html")
                                raise RuntimeError("FFmpeg is required for merging video and audio but was not found in PATH. Please install FFmpeg.")
                        else:
                            format_selector = format_id
                            logger.info(f"Using format selector: {format_selector}")
                    else:
                        # Single format ID - merge with best audio
                        format_selector = f"{format_id}+bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best"
                        logger.info(f"Merging format {format_id} with best audio")
                        
                        # Verify FFmpeg is available for merging
                        if not shutil.which('ffmpeg'):
                            logger.error("⚠️ FFmpeg is not installed or not in PATH!")
                            logger.error("   yt-dlp requires FFmpeg to merge video and audio streams.")
                            logger.error("   Install FFmpeg from: https://ffmpeg.org/download.html")
                            raise RuntimeError("FFmpeg is required for merging video and audio but was not found in PATH. Please install FFmpeg.")
                    
                    # Build command to actually download and merge
                    # For format selectors with +, ensure proper merging
                    cmd = [
                        "yt-dlp",
                        "--print-json",  # Print JSON after download
                        "--no-playlist",
                        "--no-warnings",
                        "--no-check-certificate",
                        "-f", format_selector,
                        "--merge-output-format", "mp4",  # Ensure proper merging
                        "-o", temp_file_path,  # Output to temp file
                    ]
                    # Add YouTube-specific options to bypass bot detection
                    cmd.extend(_get_youtube_options())
                    cmd.append(url)
                    logger.info(f"Downloading and merging to: {temp_file_path}")
                    logger.info(f"Format selector: {format_selector}")
                    logger.info(f"Command: yt-dlp -f '{format_selector}' --merge-output-format mp4 ...")
                    logger.info(f"Full command: {' '.join(cmd[:6])} ... -f '{format_selector}' ...")
                else:
                    # Just get metadata - use retry logic for YouTube
                    is_youtube = "youtube.com" in url or "youtu.be" in url
                    player_clients = ["ios", "android", "web", "mweb"] if is_youtube else [None]
                    last_error = None
                    metadata = None
                    
                    for client in player_clients:
                        try:
                            cmd = [
                                "yt-dlp",
                                "--dump-json",  # Output JSON metadata only
                                "--no-playlist",  # Single video only
                                "--no-warnings",
                                "--no-check-certificate",  # Avoid SSL issues
                            ]
                            
                            if client:
                                cmd.extend(_get_youtube_options(player_client=client))
                                logger.info(f"Trying YouTube metadata extraction with player_client={client}")
                            else:
                                # For non-YouTube URLs, use generic options (includes proxy, cookies)
                                cmd.extend(_get_generic_options())
                            
                            if format_id:
                                cmd.extend(["-f", f"{format_id}"])
                            else:
                                cmd.extend(["-f", settings.ytdlp_format])
                            
                            cmd.append(url)
                            
                            # Execute yt-dlp as async subprocess
                            process = await asyncio.create_subprocess_exec(
                                *cmd,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            
                            # Wait with timeout
                            timeout = settings.ytdlp_timeout_seconds
                            logger.info(f"Using timeout: {timeout}s (metadata)")
                            try:
                                stdout, stderr = await asyncio.wait_for(
                                    process.communicate(),
                                    timeout=timeout
                                )
                            except asyncio.TimeoutError:
                                process.kill()
                                await process.wait()
                                raise asyncio.TimeoutError(f"yt-dlp execution exceeded {timeout}s timeout")
                            
                            # Check exit code
                            if process.returncode != 0:
                                error_msg = stderr.decode('utf-8', errors='ignore').strip()
                                # Check if it's a retryable error (bot detection or player response failure)
                                retryable_errors = [
                                    "Sign in to confirm",
                                    "bot",
                                    "Failed to extract any player response",
                                    "Unable to extract video data"
                                ]
                                should_retry = is_youtube and any(err.lower() in error_msg.lower() for err in retryable_errors)
                                
                                if should_retry:
                                    logger.warning(f"Retryable error with player_client={client}: {error_msg[:100]}...")
                                    last_error = error_msg
                                    continue  # Try next client
                                else:
                                    # Other error, don't retry
                                    logger.error(f"yt-dlp failed with code {process.returncode}: {error_msg}")
                                    raise RuntimeError(f"yt-dlp execution failed: {error_msg or 'Unknown error'}")
                            
                            # Success! Parse and return
                            output = stdout.decode('utf-8', errors='ignore')
                            metadata = json.loads(output)
                            logger.info(f"Successfully extracted metadata (client={client or 'default'})")
                            break  # Success, exit retry loop
                            
                        except (RuntimeError, json.JSONDecodeError) as e:
                            error_str = str(e)
                            # If it's not a bot detection error, re-raise
                            if not is_youtube or ("Sign in to confirm" not in error_str and "bot" not in error_str.lower()):
                                raise
                            last_error = error_str
                            continue
                    
                    # Check if all clients failed
                    if metadata is None:
                        if last_error:
                            logger.error(f"All player clients failed for metadata extraction. Last error: {last_error}")
                            raise RuntimeError(f"yt-dlp execution failed after trying all player clients: {last_error}")
                        else:
                            raise RuntimeError("Failed to extract metadata: Unknown error")
                
                # For download path, execute directly (already set up above)
                if temp_file_path:
                    # Execute yt-dlp as async subprocess
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    # Wait with timeout
                    timeout = settings.ytdlp_timeout_seconds * 10  # Longer for downloads
                    logger.info(f"Using timeout: {timeout}s (download)")
                    try:
                        stdout, stderr = await asyncio.wait_for(
                            process.communicate(),
                            timeout=timeout
                        )
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                        raise asyncio.TimeoutError(f"yt-dlp execution exceeded {timeout}s timeout")
                    
                    # Check exit code
                    if process.returncode != 0:
                        error_msg = stderr.decode('utf-8', errors='ignore').strip()
                        logger.error(f"yt-dlp failed with code {process.returncode}: {error_msg}")
                        raise RuntimeError(f"yt-dlp execution failed: {error_msg or 'Unknown error'}")
                    
                    # Parse JSON output
                    output = stdout.decode('utf-8', errors='ignore')
                    metadata = json.loads(output)
                
                # If we downloaded a file, get the actual file path
                if temp_file_path:
                    actual_file = None
                    
                    # First, try to get from requested_downloads (most reliable)
                    if 'requested_downloads' in metadata and len(metadata['requested_downloads']) > 0:
                        downloaded_info = metadata['requested_downloads'][0]
                        actual_file = (
                            downloaded_info.get('filepath') or 
                            downloaded_info.get('filename') or
                            downloaded_info.get('_filename')
                        )
                        # Check if audio was actually merged
                        acodec = downloaded_info.get('acodec', 'none')
                        vcodec = downloaded_info.get('vcodec', 'none')
                        logger.info(f"File path from requested_downloads: {actual_file}")
                        logger.info(f"Video codec: {vcodec}, Audio codec: {acodec}")
                        if acodec == 'none' or not acodec or acodec == '-':
                            logger.warning(f"⚠️ WARNING: Downloaded file appears to have no audio! Video codec: {vcodec}, Audio codec: {acodec}")
                            logger.warning(f"Format selector was: {format_selector if 'format_selector' in locals() else 'unknown'}")
                    
                    # Also check metadata directly
                    if not actual_file:
                        actual_file = metadata.get('_filename') or metadata.get('filepath') or metadata.get('filename')
                        logger.info(f"File path from metadata: {actual_file}")
                    
                    # If found and exists, use it
                    if actual_file and os.path.exists(actual_file):
                        metadata['url'] = f"file://{actual_file}"
                        metadata['_local_file'] = actual_file
                        metadata['filesize'] = os.path.getsize(actual_file)
                        logger.info(f"✅ Downloaded and merged file: {actual_file} ({metadata['filesize']} bytes)")
                    else:
                        # Try to find the file by pattern (yt-dlp might have created it with different name)
                        import glob
                        temp_dir = tempfile.gettempdir()
                        # Look for recently created files matching our pattern
                        pattern = os.path.join(temp_dir, f"ytdlp_merge_{os.getpid()}_*.mp4")
                        logger.info(f"Searching for merged file with pattern: {pattern}")
                        files = glob.glob(pattern)
                        if files:
                            # Get most recent file (within last 60 seconds)
                            current_time = time.time()
                            recent_files = [
                                f for f in files 
                                if (current_time - os.path.getctime(f)) < 60
                            ]
                            if recent_files:
                                actual_file = max(recent_files, key=os.path.getctime)
                                metadata['url'] = f"file://{actual_file}"
                                metadata['_local_file'] = actual_file
                                metadata['filesize'] = os.path.getsize(actual_file)
                                logger.info(f"✅ Found merged file: {actual_file} ({metadata['filesize']} bytes)")
                            else:
                                logger.warning(f"⚠️ Found files but none are recent: {files}")
                        else:
                            logger.error(f"❌ Could not find merged file. Pattern: {pattern}, Metadata keys: {list(metadata.keys())}")
                            # Fallback: try to construct expected filename with different extensions
                            for ext in ['mp4', 'mkv', 'webm']:
                                expected_file = temp_file_path.replace('%(ext)s', ext)
                                if os.path.exists(expected_file):
                                    actual_file = expected_file
                                    metadata['url'] = f"file://{actual_file}"
                                    metadata['_local_file'] = actual_file
                                    metadata['filesize'] = os.path.getsize(actual_file)
                                    logger.info(f"✅ Found file at expected location: {actual_file}")
                                    break
                            
                            # If still not found, this is a critical error
                            if not actual_file:
                                logger.error(f"❌ CRITICAL: Could not find merged file after download. Temp path: {temp_file_path}")
                                logger.error(f"Metadata dump: {json.dumps(metadata, indent=2)[:500]}")
                                raise RuntimeError("Failed to locate merged video file after download. The file may not have been created properly.")
                
                logger.info(f"Successfully extracted metadata for: {metadata.get('title', 'Unknown')}")
                return self._process_metadata(metadata)
                
            finally:
                self._active_processes -= 1
    
    def _process_formats(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw yt-dlp metadata and extract format information.
        
        Args:
            raw_metadata: Raw JSON from yt-dlp
            
        Returns:
            Dictionary with video metadata and formatted list
        """
        formats = []
        raw_formats = raw_metadata.get('formats', [])
        video_formats = []
        audio_formats = []
        
        for fmt in raw_formats:
            # Determine format type
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            
            if vcodec != 'none' and acodec != 'none':
                format_type = 'combined'
            elif vcodec != 'none':
                format_type = 'video'
                video_formats.append(fmt)  # Store for later combination
            elif acodec != 'none':
                format_type = 'audio'
                audio_formats.append(fmt)  # Store for later combination
            else:
                continue  # Skip unknown formats
            
            # Build quality string
            quality = fmt.get('format_note', '')
            if not quality:
                if fmt.get('height'):
                    quality = f"{fmt.get('height')}p"
                elif fmt.get('abr'):
                    quality = f"{fmt.get('abr')}kbps"
                else:
                    quality = 'unknown'
            
            # Build resolution string
            resolution = None
            if fmt.get('width') and fmt.get('height'):
                resolution = f"{fmt.get('width')}x{fmt.get('height')}"
            
            formats.append({
                'format_id': fmt.get('format_id', ''),
                'ext': fmt.get('ext', 'unknown'),
                'quality': quality,
                'format_note': fmt.get('format_note'),
                'filesize': fmt.get('filesize'),
                'filesize_approx': fmt.get('filesize_approx'),
                'tbr': fmt.get('tbr'),
                'vcodec': vcodec if vcodec != 'none' else None,
                'acodec': acodec if acodec != 'none' else None,
                'fps': fmt.get('fps'),
                'resolution': resolution,
                'format_type': format_type,
            })
        
        # If we have separate video and audio formats, create combined formats
        # This is especially important for Facebook and other platforms that serve them separately
        if video_formats and audio_formats:
            # Find the best audio format (highest bitrate)
            best_audio = max(audio_formats, key=lambda x: x.get('abr', 0) or x.get('tbr', 0) or 0)
            best_audio_id = best_audio.get('format_id', '')
            
            # Create combined formats for each video format
            for video_fmt in video_formats:
                video_id = video_fmt.get('format_id', '')
                combined_id = f"{video_id}+{best_audio_id}"  # yt-dlp format selector syntax
                
                # Build quality string
                quality = video_fmt.get('format_note', '')
                if not quality:
                    if video_fmt.get('height'):
                        quality = f"{video_fmt.get('height')}p"
                    else:
                        quality = 'unknown'
                
                # Build resolution string
                resolution = None
                if video_fmt.get('width') and video_fmt.get('height'):
                    resolution = f"{video_fmt.get('width')}x{video_fmt.get('height')}"
                
                # Calculate combined filesize (approximate)
                video_size = video_fmt.get('filesize') or video_fmt.get('filesize_approx') or 0
                audio_size = best_audio.get('filesize') or best_audio.get('filesize_approx') or 0
                combined_size = video_size + audio_size if (video_size and audio_size) else None
                
                # Add combined format
                formats.append({
                    'format_id': combined_id,
                    'ext': video_fmt.get('ext', 'mp4'),  # Usually mp4 after merging
                    'quality': quality,
                    'format_note': f"{video_fmt.get('format_note', quality)} (with audio)",
                    'filesize': combined_size,
                    'filesize_approx': combined_size,
                    'tbr': (video_fmt.get('tbr') or 0) + (best_audio.get('tbr') or 0) or None,
                    'vcodec': video_fmt.get('vcodec'),
                    'acodec': best_audio.get('acodec'),
                    'fps': video_fmt.get('fps'),
                    'resolution': resolution,
                    'format_type': 'combined',
                })
            
            logger.info(f"Created {len(video_formats)} combined formats from {len(video_formats)} video and {len(audio_formats)} audio formats")
        
        # Extract title - try multiple fields for Instagram compatibility
        # Instagram may use different field names, check all common ones
        title = (raw_metadata.get('title') or 
                raw_metadata.get('fulltitle') or 
                raw_metadata.get('description') or
                (raw_metadata.get('uploader') and f"Video by {raw_metadata.get('uploader')}") or
                'Unknown')
        # Clean up title - remove "Video by" prefix if it's redundant
        if title.startswith('Video by Video by'):
            title = title.replace('Video by Video by', 'Video by', 1)
        
        # Extract thumbnail - Instagram may use thumbnails array or different field names
        thumbnail = (raw_metadata.get('thumbnail') or 
                    raw_metadata.get('thumb') or
                    raw_metadata.get('thumbnail_url'))
        
        # If thumbnail not found, try thumbnails array
        if not thumbnail and 'thumbnails' in raw_metadata and raw_metadata['thumbnails']:
            thumbnails = raw_metadata['thumbnails']
            if isinstance(thumbnails, list) and len(thumbnails) > 0:
                # Get the highest quality thumbnail (sorted by width)
                thumbnails_sorted = sorted([t for t in thumbnails if isinstance(t, dict) and t.get('url')], 
                                          key=lambda x: x.get('width', 0) or x.get('height', 0), 
                                          reverse=True)
                if thumbnails_sorted:
                    thumbnail = thumbnails_sorted[0].get('url')
        
        # Log for debugging Instagram metadata
        if 'instagram.com' in str(raw_metadata.get('webpage_url', '')) or 'instagram.com' in str(raw_metadata.get('url', '')):
            logger.info(f"Instagram metadata - title: {title}, thumbnail: {thumbnail[:80] if thumbnail else 'None'}")
            # Log all available fields for debugging
            available_fields = [k for k in raw_metadata.keys() if 'title' in k.lower() or 'thumb' in k.lower() or 'name' in k.lower()]
            if available_fields:
                logger.info(f"Instagram available metadata fields: {available_fields}")
        
        return {
            'title': title,
            'thumbnail': thumbnail,
            'duration': raw_metadata.get('duration'),
            'uploader': raw_metadata.get('uploader') or raw_metadata.get('channel') or raw_metadata.get('uploader_id'),
            'view_count': raw_metadata.get('view_count'),
            'formats': formats,
        }
    
    def _process_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw yt-dlp metadata into our response format.
        
        Args:
            raw_metadata: Raw JSON from yt-dlp
            
        Returns:
            Processed metadata dictionary
        """
        # Extract the best available download URL
        url = raw_metadata.get('url')
        
        # Check if we have requested_downloads (merged files)
        # This is important for formats that were merged (video+audio)
        if 'requested_downloads' in raw_metadata and raw_metadata['requested_downloads']:
            # Get the merged/downloaded file URL
            download_info = raw_metadata['requested_downloads'][0]
            url = download_info.get('url') or download_info.get('filepath')
            # If filepath is local, we need to handle it differently
            if url and not url.startswith('http'):
                # Local file path - this means yt-dlp downloaded and merged it
                # We'll need to stream from file system
                url = f"file://{url}"
        
        # If url is not direct, try formats
        if not url or ('manifest' in str(url) and not url.startswith('file://')):
            if 'formats' in raw_metadata and raw_metadata['formats']:
                # Get last format (usually best quality)
                url = raw_metadata['formats'][-1].get('url')
        
        # Check if audio is actually present in the result
        has_audio = False
        if 'requested_downloads' in raw_metadata:
            for dl in raw_metadata['requested_downloads']:
                if dl.get('acodec') and dl.get('acodec') != 'none':
                    has_audio = True
                    break
        elif raw_metadata.get('acodec') and raw_metadata.get('acodec') != 'none':
            has_audio = True
        
        return {
            'title': raw_metadata.get('title', 'Unknown'),
            'url': url,
            'file_size': raw_metadata.get('filesize') or raw_metadata.get('filesize_approx'),
            'format': raw_metadata.get('format'),
            'duration': raw_metadata.get('duration'),
            'thumbnail': raw_metadata.get('thumbnail'),
            'ext': raw_metadata.get('ext'),
            'width': raw_metadata.get('width'),
            'height': raw_metadata.get('height'),
            'has_audio': has_audio,  # Track if audio is actually present
        }
    
    @property
    def active_processes(self) -> int:
        """Get current number of active yt-dlp processes."""
        return self._active_processes

