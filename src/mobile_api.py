"""Mobile App API endpoints - Simplified API for mobile applications."""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .database import get_db, ApiToken, DownloadLog, PageView
from .service import VideoService
from .models import FormatsResponse, FormatInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mobile", tags=["mobile"])

# Global service (will be set by main.py)
video_service: Optional[VideoService] = None


# Pydantic Models for Mobile API
class TokenRequest(BaseModel):
    device_name: str
    device_info: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    expires_at: str
    message: str


class VideoRequest(BaseModel):
    url: str


class SimpleVideoResponse(BaseModel):
    success: bool
    title: str
    thumbnail: Optional[str]
    duration: Optional[float]
    formats: list


# Authentication dependency
async def verify_api_token(
    x_api_token: str = Header(None),
    db: Session = Depends(get_db)
) -> ApiToken:
    """Verify API token for mobile app."""
    if not x_api_token:
        raise HTTPException(status_code=401, detail="API token required")
    
    token = db.query(ApiToken).filter(
        ApiToken.token == x_api_token,
        ApiToken.is_active == True
    ).first()
    
    if not token:
        raise HTTPException(status_code=401, detail="Invalid or inactive API token")
    
    # Check expiration
    if token.expires_at and token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API token expired")
    
    # Update last used
    token.last_used = datetime.utcnow()
    db.commit()
    
    return token


@router.post("/register", response_model=TokenResponse)
async def register_device(
    token_request: TokenRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new mobile device and get an API token.
    
    No authentication required for registration.
    """
    try:
        # Generate secure token
        token_value = secrets.token_urlsafe(32)
        
        # Set expiration (1 year from now)
        expires_at = datetime.utcnow() + timedelta(days=365)
        
        # Create token
        api_token = ApiToken(
            token=token_value,
            name=token_request.device_name,
            device_info=token_request.device_info,
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(api_token)
        db.commit()
        db.refresh(api_token)
        
        logger.info(f"New mobile device registered: {token_request.device_name}")
        
        return TokenResponse(
            token=token_value,
            expires_at=expires_at.isoformat(),
            message="Device registered successfully. Keep this token safe!"
        )
    except Exception as e:
        logger.error(f"Failed to register device: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register device")


@router.get("/verify-token")
async def verify_token(
    token: ApiToken = Depends(verify_api_token)
):
    """Verify if the API token is valid."""
    return {
        "valid": True,
        "device_name": token.name,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        "last_used": token.last_used.isoformat() if token.last_used else None
    }


@router.post("/video/formats", response_model=SimpleVideoResponse)
async def get_video_formats(
    request: VideoRequest,
    token: ApiToken = Depends(verify_api_token),
    req: Request = None,
    db: Session = Depends(get_db)
):
    """
    Get available formats for a video URL (mobile-optimized).
    
    Returns simplified format list optimized for mobile display.
    """
    try:
        if not video_service:
            raise HTTPException(status_code=503, detail="Service not available")
        
        # Get formats
        result = await video_service.get_available_formats(
            url=request.url,
            client_ip=req.client.host if req and req.client else "mobile"
        )
        
        # Simplify formats for mobile
        simplified_formats = []
        for fmt in result['formats']:
            simplified_formats.append({
                "format_id": fmt.format_id,
                "quality": fmt.quality,
                "ext": fmt.ext,
                "filesize": fmt.filesize or fmt.filesize_approx,
                "type": fmt.format_type
            })
        
        return SimpleVideoResponse(
            success=True,
            title=result['title'],
            thumbnail=result.get('thumbnail'),
            duration=result.get('duration'),
            formats=simplified_formats
        )
    except Exception as e:
        logger.error(f"Mobile API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/download")
async def get_download_link(
    url: str,
    format_id: str,
    token: ApiToken = Depends(verify_api_token),
    db: Session = Depends(get_db)
):
    """
    Get direct download link for a video format.
    
    Returns a direct download URL that can be used in mobile apps.
    """
    try:
        if not video_service:
            raise HTTPException(status_code=503, detail="Service not available")
        
        # Get video info with download URL
        result = await video_service.get_video_info(
            url=url,
            format_id=format_id,
            client_ip="mobile"
        )
        
        return {
            "success": True,
            "title": result['title'],
            "download_url": result['url'],
            "filesize": result.get('file_size'),
            "format": result.get('format')
        }
    except Exception as e:
        logger.error(f"Mobile API download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_mobile_stats(
    token: ApiToken = Depends(verify_api_token),
    db: Session = Depends(get_db)
):
    """Get basic statistics (mobile-optimized)."""
    try:
        from sqlalchemy import func
        from datetime import date
        
        today = date.today()
        
        total_downloads = db.query(func.count(DownloadLog.id)).scalar() or 0
        today_downloads = db.query(func.count(DownloadLog.id)).filter(
            DownloadLog.download_date == today
        ).scalar() or 0
        
        return {
            "success": True,
            "total_downloads": total_downloads,
            "today_downloads": today_downloads
        }
    except Exception as e:
        logger.error(f"Mobile API stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def mobile_health_check():
    """Health check endpoint for mobile apps."""
    return {
        "status": "healthy",
        "api_version": "1.0",
        "service": "video-downloader-mobile-api"
    }


@router.post("/feedback")
async def submit_feedback(
    feedback: dict,
    token: ApiToken = Depends(verify_api_token),
    db: Session = Depends(get_db)
):
    """Submit feedback from mobile app."""
    try:
        # Log feedback (you could store this in a Feedback table)
        logger.info(f"Mobile feedback from {token.name}: {feedback}")
        
        return {
            "success": True,
            "message": "Thank you for your feedback!"
        }
    except Exception as e:
        logger.error(f"Mobile API feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

