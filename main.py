"""FastAPI application for video download service."""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator
from datetime import datetime, date
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import httpx
from src.models import VideoRequest, VideoResponse, ErrorResponse, FormatsResponse, PageResponse, HomeSectionResponse
from src.service import VideoService
from src.config import settings
from src.database import init_db, get_db, Page, PageView, DownloadLog, HomeSection, Admin, AdminRole, Theme, News
from src.auth import create_default_admin, get_password_hash
from src.admin_routes import router as admin_router
from src import mobile_api
from src.websocket_service import manager as ws_manager
from src.translation_service import TranslationService
from fastapi import WebSocket, WebSocketDisconnect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instance
video_service: VideoService = None


def create_default_home_sections(db: Session):
    """Create default home sections if none exist."""
    sections_count = db.query(HomeSection).count()
    if sections_count == 0:
        default_sections = [
            {
                "title": "Highest Quality",
                "description": "Download videos in Full HD, 2K, and 4K with original audio quality",
                "icon": "🎬",
                "order": 1,
                "is_active": True
            },
            {
                "title": "Lightning Fast",
                "description": "Instant detection and processing. Cached videos load in under 1 second",
                "icon": "⚡",
                "order": 2,
                "is_active": True
            },
            {
                "title": "Multi-Platform",
                "description": "Supports YouTube, Instagram, TikTok, Facebook, Twitter, Vimeo, and more",
                "icon": "🎯",
                "order": 3,
                "is_active": True
            }
        ]
        
        for section_data in default_sections:
            section = HomeSection(**section_data)
            db.add(section)
        
        db.commit()
        logger.info("Default home sections created")


def create_default_super_admin(db: Session):
    """Ensure the first admin is a super admin."""
    admin_count = db.query(Admin).count()
    if admin_count == 0:
        super_admin = Admin(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role=AdminRole.SUPER_ADMIN,
            is_active=True
        )
        db.add(super_admin)
        db.commit()
        print("Super Admin created: username='admin', password='admin123', role='SUPER_ADMIN'")
        print("WARNING: Please change the password immediately!")
        logger.info("Default Super Admin created")
    else:
        # Upgrade first admin to super admin if no super admin exists
        super_admin = db.query(Admin).filter(Admin.role == AdminRole.SUPER_ADMIN).first()
        if not super_admin:
            first_admin = db.query(Admin).first()
            first_admin.role = AdminRole.SUPER_ADMIN
            db.commit()
            logger.info(f"First admin '{first_admin.username}' upgraded to SUPER_ADMIN")


def create_default_themes(db: Session):
    """Create default themes if none exist."""
    theme_count = db.query(Theme).count()
    if theme_count == 0:
        default_themes = [
            {
                "name": "default",
                "display_name": "Default (Purple)",
                "primary_color": "#667eea",
                "secondary_color": "#764ba2",
                "background_color": "#f5f7fa",
                "text_color": "#333333",
                "is_active": True,
                "is_default": True
            },
            {
                "name": "blue",
                "display_name": "Ocean Blue",
                "primary_color": "#2196f3",
                "secondary_color": "#1976d2",
                "background_color": "#f5f7fa",
                "text_color": "#333333",
                "is_active": True,
                "is_default": False
            },
            {
                "name": "green",
                "display_name": "Nature Green",
                "primary_color": "#4caf50",
                "secondary_color": "#388e3c",
                "background_color": "#f5f7fa",
                "text_color": "#333333",
                "is_active": True,
                "is_default": False
            },
            {
                "name": "dark",
                "display_name": "Dark Mode",
                "primary_color": "#667eea",
                "secondary_color": "#764ba2",
                "background_color": "#1e1e1e",
                "text_color": "#ffffff",
                "is_active": True,
                "is_default": False
            }
        ]
        
        for theme_data in default_themes:
            theme = Theme(**theme_data)
            db.add(theme)
        
        db.commit()
        logger.info("Default themes created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    global video_service
    
    # Startup
    logger.info("Starting video download service...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Ensure SEO settings and News tables exist
    from src.database import SeoSettings, News, Base, engine
    Base.metadata.create_all(bind=engine, tables=[SeoSettings.__table__, News.__table__])
    logger.info("SEO settings and News tables verified")
    
    # Create default admin, home sections, themes, and translations
    from src.database import SessionLocal
    db = SessionLocal()
    try:
        create_default_super_admin(db)
        create_default_home_sections(db)
        create_default_themes(db)
        TranslationService.initialize_default_translations(db)
    finally:
        db.close()
    
    video_service = VideoService()
    
    # Set mobile API service instance
    mobile_api.video_service = video_service
    
    logger.info(f"Service running on http://{settings.host}:{settings.port}")
    logger.info(f"Max concurrent downloads: {settings.max_concurrent_downloads}")
    logger.info(f"Cache TTL: {settings.cache_ttl_seconds}s")
    logger.info(f"Rate limit: {settings.rate_limit_per_minute} req/min per IP")
    logger.info(f"Admin panel: http://{settings.host}:{settings.port}/admin")
    
    yield
    
    # Shutdown
    logger.info("Shutting down video download service...")


# Create FastAPI app
app = FastAPI(
    title="Video Download Service",
    description="High-performance video metadata extraction service using yt-dlp",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Traffic tracking middleware
@app.middleware("http")
async def track_page_views(request: Request, call_next):
    """Middleware to track page views."""
    response = await call_next(request)
    
    # Track only successful GET requests to specific paths
    if request.method == "GET" and response.status_code == 200:
        path = request.url.path
        # Track only main pages, not static assets or API calls
        if path in ["/", "/admin", "/admin/dashboard"] or path.startswith("/pages/"):
            # Log page view asynchronously
            try:
                from src.database import SessionLocal
                db = SessionLocal()
                try:
                    page_view = PageView(
                        page_path=path,
                        client_ip=request.client.host if request.client else "unknown",
                        user_agent=request.headers.get("user-agent", ""),
                        referer=request.headers.get("referer", ""),
                        view_date=date.today()
                    )
                    db.add(page_view)
                    db.commit()
                except Exception as e:
                    logger.error(f"Failed to log page view: {str(e)}")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Page view tracking error: {str(e)}")
    
    return response


# Include routers
app.include_router(admin_router)
app.include_router(mobile_api.router)


@app.get("/")
async def root(db: Session = Depends(get_db)):
    """Serve the static HTML frontend with dynamic SEO tags."""
    from src.database import SeoSettings
    import re
    
    # Get active SEO settings
    seo = db.query(SeoSettings).filter(SeoSettings.is_active == True).first()
    
    # Read the HTML file
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # If SEO settings exist, inject them
    if seo:
        # Replace title
        html_content = re.sub(
            r'<title>.*?</title>',
            f'<title>{seo.page_title}</title>',
            html_content
        )
        
        # Remove existing meta tags and add new ones
        meta_patterns = [
            r'<meta\s+name=["\']description["\'].*?>',
            r'<meta\s+name=["\']keywords["\'].*?>',
            r'<meta\s+name=["\']robots["\'].*?>',
            r'<meta\s+property=["\']og:title["\'].*?>',
            r'<meta\s+property=["\']og:description["\'].*?>',
            r'<meta\s+property=["\']og:image["\'].*?>',
            r'<meta\s+property=["\']og:url["\'].*?>',
            r'<meta\s+name=["\']twitter:card["\'].*?>',
            r'<meta\s+name=["\']twitter:title["\'].*?>',
            r'<meta\s+name=["\']twitter:description["\'].*?>',
            r'<meta\s+name=["\']twitter:image["\'].*?>',
            r'<link\s+rel=["\']canonical["\'].*?>',
        ]
        
        for pattern in meta_patterns:
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)
        
        # Escape HTML entities for meta tags
        from html import escape
        
        # Add SEO meta tags before closing head tag
        seo_tags = f'''
    <meta name="description" content="{escape(seo.meta_description)}">
    <meta name="robots" content="{escape(seo.robots)}">'''
        
        if seo.meta_keywords:
            seo_tags += f'\n    <meta name="keywords" content="{escape(seo.meta_keywords)}">'
        
        # Open Graph tags
        og_title = escape(seo.og_title or seo.page_title)
        og_desc = escape(seo.og_description or seo.meta_description)
        seo_tags += f'''
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{og_desc}">'''
        
        if seo.og_image:
            seo_tags += f'\n    <meta property="og:image" content="{escape(seo.og_image)}">'
        if seo.og_url:
            seo_tags += f'\n    <meta property="og:url" content="{escape(seo.og_url)}">'
        
        # Twitter Card tags
        twitter_title = escape(seo.twitter_title or seo.page_title)
        twitter_desc = escape(seo.twitter_description or seo.meta_description)
        seo_tags += f'''
    <meta name="twitter:card" content="{escape(seo.twitter_card)}">
    <meta name="twitter:title" content="{twitter_title}">
    <meta name="twitter:description" content="{twitter_desc}">'''
        
        if seo.twitter_image:
            seo_tags += f'\n    <meta name="twitter:image" content="{escape(seo.twitter_image)}">'
        
        # Canonical URL
        if seo.canonical_url:
            seo_tags += f'\n    <link rel="canonical" href="{escape(seo.canonical_url)}">'
        
        # Insert before closing </head>
        html_content = html_content.replace('</head>', seo_tags + '\n</head>')
    
    return HTMLResponse(content=html_content)


@app.get("/admin")
async def admin_panel():
    """Serve admin login panel."""
    return FileResponse("static/admin/index.html")


@app.get("/admin/dashboard")
async def admin_dashboard():
    """Serve admin dashboard."""
    return FileResponse("static/admin/dashboard.html")


@app.get("/api/pages")
async def get_published_pages(db: Session = Depends(get_db)):
    """Get all published pages (public endpoint)."""
    pages = db.query(Page).filter(
        Page.is_published == True
    ).order_by(Page.title).all()
    
    return [
        {
            "id": page.id,
            "slug": page.slug,
            "title": page.title,
            "is_published": page.is_published
        }
        for page in pages
    ]


@app.get("/api/home-sections")
async def get_public_home_sections(db: Session = Depends(get_db)):
    """Get all active home sections (public endpoint)."""
    sections = db.query(HomeSection).filter(
        HomeSection.is_active == True
    ).order_by(HomeSection.order).all()
    
    return [
        {
            "id": section.id,
            "title": section.title,
            "description": section.description,
            "icon": section.icon,
            "order": section.order
        }
        for section in sections
    ]


@app.get("/api/news")
async def get_public_news(db: Session = Depends(get_db)):
    """Get all active news items (public endpoint)."""
    news_items = db.query(News).filter(
        News.is_active == True
    ).order_by(News.news_date.desc(), News.order).limit(20).all()
    
    return [
        {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "news_date": item.news_date.isoformat(),
            "order": item.order
        }
        for item in news_items
    ]


@app.get("/api/seo")
async def get_public_seo(db: Session = Depends(get_db)):
    """Get active SEO settings for frontend (public endpoint)."""
    from src.database import SeoSettings
    seo = db.query(SeoSettings).filter(SeoSettings.is_active == True).first()
    if not seo:
        return {
            "page_title": "Video Downloader - Download HD Videos from Any Platform",
            "meta_description": "Download high-quality videos from YouTube, Instagram, TikTok, Facebook, Twitter, and more.",
            "meta_keywords": "video downloader, youtube downloader, instagram downloader",
            "og_title": "Video Downloader - Download HD Videos from Any Platform",
            "og_description": "Download high-quality videos from YouTube, Instagram, TikTok, Facebook, Twitter, and more.",
            "robots": "index, follow"
        }
    
    return {
        "page_title": seo.page_title,
        "meta_description": seo.meta_description,
        "meta_keywords": seo.meta_keywords,
        "og_title": seo.og_title or seo.page_title,
        "og_description": seo.og_description or seo.meta_description,
        "og_image": seo.og_image,
        "og_url": seo.og_url,
        "twitter_card": seo.twitter_card,
        "twitter_title": seo.twitter_title or seo.page_title,
        "twitter_description": seo.twitter_description or seo.meta_description,
        "twitter_image": seo.twitter_image,
        "canonical_url": seo.canonical_url,
        "robots": seo.robots
    }


@app.websocket("/ws/admin/{admin_id}")
async def websocket_endpoint(websocket: WebSocket, admin_id: int):
    """WebSocket endpoint for real-time notifications."""
    await ws_manager.connect(websocket, admin_id)
    
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            
            # Echo back for testing
            await websocket.send_json({
                "type": "pong",
                "message": "Connection alive",
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, admin_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        ws_manager.disconnect(websocket, admin_id)


@app.get("/page/{slug}", response_model=PageResponse)
async def get_public_page(slug: str, db: Session = Depends(get_db)):
    """Get a published page by slug."""
    page = db.query(Page).filter(
        Page.slug == slug,
        Page.is_published == True
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return page


@app.get("/pages/{slug}")
async def view_public_page(slug: str):
    """Serve page viewer."""
    return FileResponse("static/pages/view.html")


@app.post("/api/formats", response_model=FormatsResponse)
async def get_available_formats(request: VideoRequest, req: Request):
    """
    Get all available video and audio formats for a given URL.
    
    Args:
        request: Video request containing URL
        req: FastAPI request object (for IP extraction)
        
    Returns:
        Video metadata and list of all available formats
        
    Raises:
        HTTPException: On errors (rate limit, invalid URL, etc.)
    """
    try:
        # Get client IP
        client_ip = req.client.host
        
        # Process request
        logger.info(f"Fetching formats from {client_ip}: {request.url}")
        
        result = await video_service.get_available_formats(
            url=str(request.url),
            client_ip=client_ip
        )
        
        return FormatsResponse(
            success=True,
            title=result['title'],
            thumbnail=result.get('thumbnail'),
            duration=result.get('duration'),
            uploader=result.get('uploader'),
            view_count=result.get('view_count'),
            formats=result['formats']
        )
        
    except ValueError as e:
        # Rate limit or validation errors
        logger.warning(f"Client error: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    
    except asyncio.TimeoutError as e:
        logger.error(f"Timeout error: {str(e)}")
        raise HTTPException(status_code=504, detail="Request timeout: video processing took too long")
    
    except Exception as e:
        error_msg = str(e)
        # Truncate very long error messages to prevent issues
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."
        logger.error(f"Error fetching formats: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch formats: {error_msg}")


@app.get("/api/download")
async def download_video(
    url: str,
    format_id: str,
    title: str,
    ext: str,
    format_type: str = "combined",  # Track which tab the format came from
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Proxy download endpoint that streams the video through the backend.
    This ensures proper download behavior with progress bar and save dialog.
    
    Args:
        url: Video URL
        format_id: Format ID to download
        title: Video title for filename
        ext: File extension
        request: Request object for tracking
        db: Database session
        
    Returns:
        StreamingResponse with the video file
    """
    filesize = None
    success = True
    error_msg = None
    
    try:
        # Get the direct download URL using yt-dlp
        # Always ensure audio is merged for "combined" tab downloads
        # This fixes the issue where "combined" formats might actually be video-only
        ensure_audio = (format_type == "combined")  # Only merge for "Video + Audio" tab
        
        result = await video_service.get_video_info(
            url=url,
            format_id=format_id,
            client_ip="download",
            ensure_audio=ensure_audio  # Merge audio only for combined tab
        )
        
        download_url = result['url']
        filesize = result.get('file_size')
        
        # Sanitize filename (remove invalid characters but keep Unicode)
        # Remove only truly invalid filename characters: \ / : * ? " < > |
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        safe_title = title
        for char in invalid_chars:
            safe_title = safe_title.replace(char, '')
        safe_title = safe_title.strip()[:200]  # Limit length
        
        filename = f"{safe_title}.{ext}"
        
        # Encode filename for HTTP header (RFC 5987)
        # Use UTF-8 encoding and URL-encode the filename
        encoded_filename = quote(filename, safe='')
        
        logger.info(f"Starting download stream: {filename}")
        
        # Stream the file through our backend
        async def stream_video() -> AsyncIterator[bytes]:
            """Stream video content from external URL or local file."""
            # Check if it's a local file (yt-dlp downloaded and merged it)
            if download_url.startswith('file://'):
                import aiofiles
                file_path = download_url[7:]  # Remove 'file://' prefix
                async with aiofiles.open(file_path, 'rb') as f:
                    while True:
                        chunk = await f.read(1024 * 1024)  # 1MB chunks
                        if not chunk:
                            break
                        yield chunk
                # Clean up temporary file
                try:
                    import os
                    os.remove(file_path)
                except:
                    pass
            else:
                # Stream from external URL
                async with httpx.AsyncClient(timeout=300.0) as client:
                    async with client.stream('GET', download_url) as response:
                        response.raise_for_status()
                        async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                            yield chunk
        
        # Log successful download
        try:
            download_log = DownloadLog(
                video_url=url,
                video_title=title,
                format_id=format_id,
                file_size=filesize,
                client_ip=request.client.host if request and request.client else "unknown",
                user_agent=request.headers.get("user-agent", "") if request else "",
                success=True,
                download_date=date.today()
            )
            db.add(download_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log download: {str(e)}")
        
        # Return streaming response with proper headers
        # Use RFC 5987 format for Unicode filenames
        return StreamingResponse(
            stream_video(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Cache-Control": "no-cache",
            }
        )
        
    except httpx.HTTPError as e:
        success = False
        error_msg = str(e)
        logger.error(f"HTTP error during download: {error_msg}")
        
        # Log failed download
        try:
            download_log = DownloadLog(
                video_url=url,
                video_title=title,
                format_id=format_id,
                file_size=filesize,
                client_ip=request.client.host if request and request.client else "unknown",
                user_agent=request.headers.get("user-agent", "") if request else "",
                success=False,
                error_message=error_msg,
                download_date=date.today()
            )
            db.add(download_log)
            db.commit()
        except Exception as log_error:
            logger.error(f"Failed to log download error: {str(log_error)}")
        
        raise HTTPException(status_code=502, detail=f"Failed to fetch video: {error_msg}")
    except RuntimeError as e:
        # Check if it's an FFmpeg-related error
        error_msg = str(e)
        if "FFmpeg" in error_msg or "ffmpeg" in error_msg.lower():
            user_friendly_msg = "FFmpeg is required to merge video and audio but is not installed. Please install FFmpeg and add it to your system PATH. Visit https://ffmpeg.org/download.html for installation instructions."
            logger.error(f"FFmpeg error: {error_msg}")
            raise HTTPException(
                status_code=503, 
                detail=user_friendly_msg
            )
        else:
            logger.error(f"Runtime error during download: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Download failed: {error_msg}")
    
    except Exception as e:
        success = False
        error_msg = str(e)
        logger.error(f"Download error: {error_msg}")
        
        # Log failed download
        try:
            download_log = DownloadLog(
                video_url=url,
                video_title=title,
                format_id=format_id,
                file_size=filesize,
                client_ip=request.client.host if request and request.client else "unknown",
                user_agent=request.headers.get("user-agent", "") if request else "",
                success=False,
                error_message=error_msg,
                download_date=date.today()
            )
            db.add(download_log)
            db.commit()
        except Exception as log_error:
            logger.error(f"Failed to log download error: {str(log_error)}")
        
        raise HTTPException(status_code=500, detail=f"Download failed: {error_msg}")


@app.post("/api/video", response_model=VideoResponse)
async def get_video_info(request: VideoRequest, req: Request):
    """
    Extract video metadata and download link for a specific format.
    
    Args:
        request: Video request containing URL and optional format_id
        req: FastAPI request object (for IP extraction)
        
    Returns:
        Video metadata including download link
        
    Raises:
        HTTPException: On errors (rate limit, invalid URL, etc.)
    """
    try:
        # Get client IP
        client_ip = req.client.host
        
        # Process request
        logger.info(f"Processing video request from {client_ip}: {request.url}")
        
        result = await video_service.get_video_info(
            url=str(request.url),
            format_id=request.format_id,
            client_ip=client_ip
        )
        
        return VideoResponse(
            success=True,
            title=result['title'],
            url=result['url'],
            file_size=result.get('file_size'),
            format=result.get('format'),
            duration=result.get('duration'),
            thumbnail=result.get('thumbnail')
        )
        
    except ValueError as e:
        # Rate limit or validation errors
        logger.warning(f"Client error: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    
    except asyncio.TimeoutError as e:
        logger.error(f"Timeout error: {str(e)}")
        raise HTTPException(status_code=504, detail="Request timeout: video processing took too long")
    
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint with service statistics."""
    stats = video_service.get_cache_stats()
    return {
        "status": "healthy",
        "service": "video-download-api",
        "stats": stats
    }


@app.post("/api/cache/clear")
async def clear_cache():
    """Clear the cache (admin endpoint - add auth in production)."""
    video_service.clear_cache()
    return {"success": True, "message": "Cache cleared"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    
    error_detail = "; ".join(error_messages)
    logger.warning(f"Validation error: {error_detail}")
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            success=False,
            error=error_detail,
            details=errors
        ).model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.detail,
            details=None
        ).model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure all errors return JSON."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error=f"Internal server error: {str(exc)}",
            details=None
        ).model_dump()
    )


# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static directory not found - will be created")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # Set to True for development
        log_level="info",
        access_log=True
    )

