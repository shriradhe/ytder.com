"""Admin API routes for CMS management."""
import logging
import shutil
import os
from pathlib import Path
from typing import List
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, or_
from .database import (
    get_db, Page, HomeSection, DownloadLog, PageView, Settings,
    Admin, AdminRole, Theme, Translation, Notification, EmailNotification, ApiToken,
    SeoSettings, News, DATABASE_URL, PROJECT_ROOT, DATA_DIR
)
from .auth import get_current_admin, verify_password, create_access_token, get_password_hash
from .models import (
    AdminLogin, AdminToken, PageCreate, PageUpdate,
    PageResponse, PageListItem,
    HomeSectionCreate, HomeSectionUpdate, HomeSectionResponse,
    DailyStats, MonthlyStats, OverallStats,
    SettingCreate, SettingUpdate, SettingResponse,
    PasswordChange,
    AdminCreate, AdminUpdate, AdminResponse,
    ThemeCreate, ThemeUpdate, ThemeResponse,
    TranslationCreate, TranslationUpdate, TranslationResponse,
    NotificationResponse, EmailNotificationRequest, EmailNotificationResponse,
    ApiTokenResponse, SearchFilters,
    SeoSettingsCreate, SeoSettingsUpdate, SeoSettingsResponse,
    NewsCreate, NewsUpdate, NewsResponse
)
# Lazy import for email service to avoid startup errors with fastapi-mail compatibility
try:
    from .email_service import EmailService
except ImportError as e:
    logger.warning(f"Email service not available: {e}")
    EmailService = None
from .export_service import ExportService
from .translation_service import TranslationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================
# AUTHENTICATION
# ============================================

@router.post("/login", response_model=AdminToken)
async def admin_login(login_data: AdminLogin, db: Session = Depends(get_db)):
    """Admin login endpoint."""
    from .database import Admin
    
    admin = db.query(Admin).filter(Admin.username == login_data.username).first()
    
    if not admin or not verify_password(login_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )
    
    access_token = create_access_token(data={"sub": admin.username})
    logger.info(f"Admin login successful: {admin.username}")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Change admin password."""
    if not verify_password(password_data.old_password, current_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_admin.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    logger.info(f"Password changed for admin: {current_admin.username}")
    return {"success": True, "message": "Password changed successfully"}


# ============================================
# PAGE MANAGEMENT
# ============================================

@router.get("/pages", response_model=List[PageListItem])
async def list_pages(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all pages."""
    pages = db.query(Page).order_by(Page.updated_at.desc()).all()
    return pages


@router.get("/pages/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get a specific page by ID."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("/pages", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    page_data: PageCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create a new page."""
    existing = db.query(Page).filter(Page.slug == page_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page with slug '{page_data.slug}' already exists"
        )
    
    page = Page(**page_data.model_dump())
    db.add(page)
    db.commit()
    db.refresh(page)
    
    logger.info(f"Page created: {page.slug} by {current_admin.username}")
    return page


@router.put("/pages/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: int,
    page_data: PageUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update an existing page."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    update_data = page_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(page, key, value)
    
    db.commit()
    db.refresh(page)
    
    logger.info(f"Page updated: {page.slug} by {current_admin.username}")
    return page


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete a page."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    slug = page.slug
    db.delete(page)
    db.commit()
    
    logger.info(f"Page deleted: {slug} by {current_admin.username}")
    return None


# ============================================
# HOME SECTIONS MANAGEMENT
# ============================================

@router.get("/home-sections", response_model=List[HomeSectionResponse])
async def list_home_sections(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all home sections."""
    sections = db.query(HomeSection).order_by(HomeSection.order).all()
    return sections


@router.get("/home-sections/{section_id}", response_model=HomeSectionResponse)
async def get_home_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get a specific home section by ID."""
    section = db.query(HomeSection).filter(HomeSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Home section not found")
    return section


@router.post("/home-sections", response_model=HomeSectionResponse, status_code=status.HTTP_201_CREATED)
async def create_home_section(
    section_data: HomeSectionCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create a new home section."""
    section = HomeSection(**section_data.model_dump())
    db.add(section)
    db.commit()
    db.refresh(section)
    
    logger.info(f"Home section created: {section.title} by {current_admin.username}")
    return section


@router.put("/home-sections/{section_id}", response_model=HomeSectionResponse)
async def update_home_section(
    section_id: int,
    section_data: HomeSectionUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update an existing home section."""
    section = db.query(HomeSection).filter(HomeSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Home section not found")
    
    update_data = section_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(section, key, value)
    
    db.commit()
    db.refresh(section)
    
    logger.info(f"Home section updated: {section.title} by {current_admin.username}")
    return section


@router.delete("/home-sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_home_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete a home section."""
    section = db.query(HomeSection).filter(HomeSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Home section not found")
    
    title = section.title
    db.delete(section)
    db.commit()
    
    logger.info(f"Home section deleted: {title} by {current_admin.username}")
    return None


# ============================================
# STATISTICS & ANALYTICS
# ============================================

@router.get("/stats/overall", response_model=OverallStats)
async def get_overall_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get overall statistics."""
    today = date.today()
    first_day_of_month = today.replace(day=1)
    
    # Total counts
    total_downloads = db.query(func.count(DownloadLog.id)).scalar() or 0
    total_page_views = db.query(func.count(PageView.id)).scalar() or 0
    
    # Today's counts
    today_downloads = db.query(func.count(DownloadLog.id)).filter(
        DownloadLog.download_date == today
    ).scalar() or 0
    
    today_views = db.query(func.count(PageView.id)).filter(
        PageView.view_date == today
    ).scalar() or 0
    
    # This month's counts
    this_month_downloads = db.query(func.count(DownloadLog.id)).filter(
        DownloadLog.download_date >= first_day_of_month
    ).scalar() or 0
    
    this_month_views = db.query(func.count(PageView.id)).filter(
        PageView.view_date >= first_day_of_month
    ).scalar() or 0
    
    return OverallStats(
        total_downloads=total_downloads,
        total_page_views=total_page_views,
        today_downloads=today_downloads,
        today_views=today_views,
        this_month_downloads=this_month_downloads,
        this_month_views=this_month_views
    )


@router.get("/stats/daily", response_model=List[DailyStats])
async def get_daily_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get daily statistics for the last N days."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # Get daily download counts
    download_counts = db.query(
        DownloadLog.download_date,
        func.count(DownloadLog.id).label('count')
    ).filter(
        DownloadLog.download_date >= start_date
    ).group_by(DownloadLog.download_date).all()
    
    # Get daily page view counts
    view_counts = db.query(
        PageView.view_date,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.view_date >= start_date
    ).group_by(PageView.view_date).all()
    
    # Create a dictionary for quick lookup
    downloads_dict = {str(d.download_date): d.count for d in download_counts}
    views_dict = {str(v.view_date): v.count for v in view_counts}
    
    # Generate complete date range
    stats = []
    current_date = start_date
    while current_date <= end_date:
        date_str = str(current_date)
        stats.append(DailyStats(
            date=date_str,
            downloads=downloads_dict.get(date_str, 0),
            page_views=views_dict.get(date_str, 0)
        ))
        current_date += timedelta(days=1)
    
    return stats


@router.get("/stats/monthly", response_model=List[MonthlyStats])
async def get_monthly_stats(
    months: int = 12,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get monthly statistics for the last N months."""
    # Get monthly download counts
    download_counts = db.query(
        extract('year', DownloadLog.download_date).label('year'),
        extract('month', DownloadLog.download_date).label('month'),
        func.count(DownloadLog.id).label('count')
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    # Get monthly page view counts
    view_counts = db.query(
        extract('year', PageView.view_date).label('year'),
        extract('month', PageView.view_date).label('month'),
        func.count(PageView.id).label('count')
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    # Create dictionaries for quick lookup
    downloads_dict = {f"{int(d.year)}-{int(d.month):02d}": d.count for d in download_counts}
    views_dict = {f"{int(v.year)}-{int(v.month):02d}": v.count for v in view_counts}
    
    # Generate last N months
    stats = []
    current_date = date.today().replace(day=1)
    for i in range(months):
        month_key = current_date.strftime("%Y-%m")
        stats.insert(0, MonthlyStats(
            month=month_key,
            downloads=downloads_dict.get(month_key, 0),
            page_views=views_dict.get(month_key, 0)
        ))
        # Go to previous month
        if current_date.month == 1:
            current_date = current_date.replace(year=current_date.year-1, month=12)
        else:
            current_date = current_date.replace(month=current_date.month-1)
    
    return stats


# ============================================
# SETTINGS MANAGEMENT
# ============================================

@router.get("/settings", response_model=List[SettingResponse])
async def list_settings(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all settings."""
    settings = db.query(Settings).all()
    return settings


@router.get("/settings/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get a specific setting by key."""
    setting = db.query(Settings).filter(Settings.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting


@router.post("/settings", response_model=SettingResponse, status_code=status.HTTP_201_CREATED)
async def create_setting(
    setting_data: SettingCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create a new setting."""
    existing = db.query(Settings).filter(Settings.key == setting_data.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Setting with key '{setting_data.key}' already exists"
        )
    
    setting = Settings(**setting_data.model_dump())
    db.add(setting)
    db.commit()
    db.refresh(setting)
    
    logger.info(f"Setting created: {setting.key} by {current_admin.username}")
    return setting


@router.put("/settings/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    setting_data: SettingUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update an existing setting."""
    setting = db.query(Settings).filter(Settings.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    update_data = setting_data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(setting, k, v)
    
    db.commit()
    db.refresh(setting)
    
    logger.info(f"Setting updated: {setting.key} by {current_admin.username}")
    return setting


@router.delete("/settings/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    key: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete a setting."""
    setting = db.query(Settings).filter(Settings.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    db.delete(setting)
    db.commit()
    
    logger.info(f"Setting deleted: {key} by {current_admin.username}")
    return None


# ============================================
# DATABASE BACKUP
# ============================================

@router.post("/database/backup")
async def backup_database(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create a database backup."""
    try:
        # Use DATA_DIR directly - this is the standard location after reorganization
        db_path = (DATA_DIR / "video_downloader.db").resolve()
        
        # If not found in standard location, try to extract from DATABASE_URL
        if not db_path.exists() and "sqlite" in DATABASE_URL:
            # Extract path from DATABASE_URL as fallback
            db_path_str = DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
            # Normalize Windows paths (handle backslashes)
            if "\\" in db_path_str or (db_path_str.startswith("/") and len(db_path_str) > 1 and db_path_str[1] != "/"):
                db_path = Path(db_path_str).resolve()
            else:
                db_path = (PROJECT_ROOT / db_path_str).resolve()
        
        logger.info(f"Attempting backup from database path: {db_path}")
        logger.info(f"DATA_DIR: {DATA_DIR}, PROJECT_ROOT: {PROJECT_ROOT}")
        logger.info(f"Database path exists: {db_path.exists()}")
        
        if not db_path.exists():
            # List available .db files for debugging
            available_dbs = list(DATA_DIR.glob("*.db"))
            logger.error(f"Database not found at {db_path}. Available DB files in data/: {[str(f) for f in available_dbs]}")
            raise HTTPException(
                status_code=404, 
                detail=f"Database file not found at: {db_path}. Available files in data/: {[f.name for f in available_dbs] if available_dbs else 'none'}"
            )
        
        # Create backups directory in data/backups/
        backup_dir = DATA_DIR / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Backup directory: {backup_dir}")
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = backup_dir / backup_filename
        
        # Copy database file
        shutil.copy2(str(db_path), str(backup_path))
        
        file_size = backup_path.stat().st_size
        
        logger.info(f"Database backup created: {backup_filename} by {current_admin.username}")
        
        return {
            "success": True,
            "message": "Database backup created successfully",
            "filename": backup_filename,
            "path": str(backup_path),
            "size": file_size,
            "timestamp": timestamp
        }
    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/database/backups")
async def list_backups(
    current_admin = Depends(get_current_admin)
):
    """List all database backups."""
    try:
        backup_dir = DATA_DIR / "backups"
        if not backup_dir.exists():
            return {"backups": []}
        
        backups = []
        for filepath in backup_dir.glob("*.db"):
            if filepath.is_file():
                stat = filepath.stat()
                backups.append({
                    "filename": filepath.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {"backups": backups}
    except Exception as e:
        logger.error(f"Failed to list backups: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.post("/database/restore")
async def restore_database(
    request: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Restore database from a backup file."""
    try:
        # Extract backup filename from request
        backup_filename = request.get("backup_filename")
        if not backup_filename:
            raise HTTPException(status_code=400, detail="backup_filename is required")
        
        # Only allow super admins to restore database
        if current_admin.role != AdminRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=403, 
                detail="Only super admins can restore the database"
            )
        
        # Validate backup filename (prevent directory traversal)
        if ".." in backup_filename or "/" in backup_filename or "\\" in backup_filename:
            raise HTTPException(status_code=400, detail="Invalid backup filename")
        
        # Get backup file path
        backup_dir = DATA_DIR / "backups"
        backup_path = backup_dir / backup_filename
        
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail=f"Backup file not found: {backup_filename}")
        
        # Verify it's a .db file
        if not backup_path.suffix == ".db":
            raise HTTPException(status_code=400, detail="Invalid backup file type")
        
        # Get current database path
        db_path = (DATA_DIR / "video_downloader.db").resolve()
        
        # If not found in standard location, try to extract from DATABASE_URL
        if not db_path.exists() and "sqlite" in DATABASE_URL:
            db_path_str = DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
            if "\\" in db_path_str or (db_path_str.startswith("/") and len(db_path_str) > 1 and db_path_str[1] != "/"):
                db_path = Path(db_path_str).resolve()
            else:
                db_path = (PROJECT_ROOT / db_path_str).resolve()
        
        logger.info(f"Restoring database from {backup_path} to {db_path} by {current_admin.username}")
        
        # Create a safety backup of current database before restoring
        if db_path.exists():
            safety_backup_path = backup_dir / f"safety_backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(str(db_path), str(safety_backup_path))
            logger.info(f"Created safety backup: {safety_backup_path.name}")
        
        # Close all database connections before restoring
        # SQLAlchemy engine will handle this, but we should close the session
        db.close()
        
        # Copy backup file to database location
        shutil.copy2(str(backup_path), str(db_path))
        
        # Verify the restore was successful
        if not db_path.exists() or db_path.stat().st_size == 0:
            raise HTTPException(status_code=500, detail="Restore failed: database file is invalid or empty")
        
        file_size = db_path.stat().st_size
        
        logger.info(f"Database restored successfully from {backup_filename} by {current_admin.username}")
        
        return {
            "success": True,
            "message": "Database restored successfully",
            "backup_filename": backup_filename,
            "database_path": str(db_path),
            "size": file_size,
            "note": "Please restart the application for changes to take effect"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database restore failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


# ============================================
# SEO MANAGEMENT
# ============================================

@router.get("/seo", response_model=SeoSettingsResponse)
async def get_seo_settings(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get current SEO settings."""
    try:
        # Ensure table exists
        from src.database import Base, engine
        Base.metadata.create_all(bind=engine, tables=[SeoSettings.__table__])
        
        seo = db.query(SeoSettings).filter(SeoSettings.is_active == True).first()
        if not seo:
            # Create default SEO settings
            seo = SeoSettings(
                page_title="Video Downloader - Download HD Videos from Any Platform",
                meta_description="Download high-quality videos from YouTube, Instagram, TikTok, Facebook, Twitter, and more. Fast, free, and easy video downloader.",
                meta_keywords="video downloader, youtube downloader, instagram downloader, tiktok downloader, free video download",
                og_title="Video Downloader - Download HD Videos from Any Platform",
                og_description="Download high-quality videos from YouTube, Instagram, TikTok, Facebook, Twitter, and more.",
                robots="index, follow",
                is_active=True,
                updated_by=current_admin.id
            )
            db.add(seo)
            db.commit()
            db.refresh(seo)
            logger.info("Default SEO settings created")
        
        return seo
    except Exception as e:
        logger.error(f"Error getting SEO settings: {str(e)}", exc_info=True)
        # Return default settings if there's an error
        from src.models import SeoSettingsResponse
        from datetime import datetime
        return SeoSettingsResponse(
            id=0,
            page_title="Video Downloader - Download HD Videos from Any Platform",
            meta_description="Download high-quality videos from YouTube, Instagram, TikTok, Facebook, Twitter, and more.",
            meta_keywords="video downloader, youtube downloader, instagram downloader",
            og_title="Video Downloader - Download HD Videos from Any Platform",
            og_description="Download high-quality videos from YouTube, Instagram, TikTok, Facebook, Twitter, and more.",
            robots="index, follow",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )


@router.get("/seo/public")
async def get_public_seo_settings(db: Session = Depends(get_db)):
    """Get active SEO settings for frontend (public endpoint)."""
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


@router.post("/seo", response_model=SeoSettingsResponse)
async def create_seo_settings(
    seo_data: SeoSettingsCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create or update SEO settings."""
    # Deactivate existing SEO settings
    existing = db.query(SeoSettings).filter(SeoSettings.is_active == True).all()
    for seo in existing:
        seo.is_active = False
    
    # Create new SEO settings
    seo = SeoSettings(
        **seo_data.model_dump(),
        updated_by=current_admin.id
    )
    db.add(seo)
    db.commit()
    db.refresh(seo)
    
    logger.info(f"SEO settings created/updated by {current_admin.username}")
    return seo


@router.put("/seo/{seo_id}", response_model=SeoSettingsResponse)
async def update_seo_settings(
    seo_id: int,
    seo_data: SeoSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update SEO settings."""
    seo = db.query(SeoSettings).filter(SeoSettings.id == seo_id).first()
    if not seo:
        raise HTTPException(status_code=404, detail="SEO settings not found")
    
    # Update fields
    update_data = seo_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(seo, key, value)
    
    seo.updated_by = current_admin.id
    seo.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(seo)
    
    logger.info(f"SEO settings updated by {current_admin.username}")
    return seo


@router.get("/seo/history")
async def get_seo_history(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get SEO settings history."""
    seo_list = db.query(SeoSettings).order_by(SeoSettings.updated_at.desc()).limit(10).all()
    return [
        {
            "id": seo.id,
            "page_title": seo.page_title,
            "is_active": seo.is_active,
            "updated_at": seo.updated_at.isoformat(),
            "updated_by": seo.updated_by
        }
        for seo in seo_list
    ]


# ============================================
# ADMIN USER MANAGEMENT (Multiple Admins)
# ============================================

@router.get("/admins", response_model=List[AdminResponse])
async def list_admins(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all admin users (Super Admin only)."""
    if current_admin.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admins can list users")
    
    admins = db.query(Admin).all()
    return admins


@router.post("/admins", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_data: AdminCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create a new admin user (Super Admin only)."""
    if current_admin.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admins can create users")
    
    # Check if username exists
    existing = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    existing_email = db.query(Admin).filter(Admin.email == admin_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create admin
    new_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=get_password_hash(admin_data.password),
        role=AdminRole[admin_data.role.upper()] if admin_data.role else AdminRole.ADMIN
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    logger.info(f"Admin created: {new_admin.username} by {current_admin.username}")
    return new_admin


@router.put("/admins/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    admin_data: AdminUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update an admin user."""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Only Super Admin can update roles or other admins
    if current_admin.role != AdminRole.SUPER_ADMIN and admin_id != current_admin.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    update_data = admin_data.model_dump(exclude_unset=True)
    
    # Only Super Admin can change roles
    if 'role' in update_data and current_admin.role != AdminRole.SUPER_ADMIN:
        del update_data['role']
    
    for key, value in update_data.items():
        if key == 'role':
            setattr(admin, key, AdminRole[value.upper()])
        else:
            setattr(admin, key, value)
    
    db.commit()
    db.refresh(admin)
    
    logger.info(f"Admin updated: {admin.username} by {current_admin.username}")
    return admin


@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete an admin user (Super Admin only)."""
    if current_admin.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admins can delete users")
    
    if admin_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    username = admin.username
    db.delete(admin)
    db.commit()
    
    logger.info(f"Admin deleted: {username} by {current_admin.username}")
    return None


# ============================================
# THEME MANAGEMENT
# ============================================

@router.get("/themes", response_model=List[ThemeResponse])
async def list_themes(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all themes."""
    themes = db.query(Theme).all()
    return themes


@router.post("/themes", response_model=ThemeResponse, status_code=status.HTTP_201_CREATED)
async def create_theme(
    theme_data: ThemeCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create a new theme."""
    existing = db.query(Theme).filter(Theme.name == theme_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Theme name already exists")
    
    theme = Theme(**theme_data.model_dump())
    db.add(theme)
    db.commit()
    db.refresh(theme)
    
    logger.info(f"Theme created: {theme.name} by {current_admin.username}")
    return theme


@router.put("/themes/{theme_id}", response_model=ThemeResponse)
async def update_theme(
    theme_id: int,
    theme_data: ThemeUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update a theme."""
    theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    
    update_data = theme_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(theme, key, value)
    
    db.commit()
    db.refresh(theme)
    
    logger.info(f"Theme updated: {theme.name} by {current_admin.username}")
    return theme


# ============================================
# TRANSLATION/i18n MANAGEMENT
# ============================================

@router.get("/translations/{language_code}")
async def get_translations(
    language_code: str,
    db: Session = Depends(get_db)
):
    """Get all translations for a language."""
    translations = TranslationService.get_translations(language_code, db)
    return {"language": language_code, "translations": translations}


@router.post("/translations", response_model=TranslationResponse, status_code=status.HTTP_201_CREATED)
async def create_translation(
    translation_data: TranslationCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create or update a translation."""
    success = TranslationService.save_translation(
        language=translation_data.language_code,
        key=translation_data.key,
        value=translation_data.value,
        db=db
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save translation")
    
    translation = db.query(Translation).filter(
        Translation.language_code == translation_data.language_code,
        Translation.key == translation_data.key
    ).first()
    
    logger.info(f"Translation saved: {translation_data.key} by {current_admin.username}")
    return translation


@router.get("/translations")
async def list_all_translations(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all translations."""
    translations = db.query(Translation).all()
    return translations


@router.get("/languages")
async def get_available_languages():
    """Get list of available languages."""
    return {"languages": TranslationService.get_available_languages()}


# ============================================
# NOTIFICATIONS
# ============================================

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get notifications for current admin."""
    query = db.query(Notification).filter(Notification.admin_id == current_admin.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    return notifications


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Mark notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.admin_id == current_admin.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return {"success": True}


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.admin_id == current_admin.id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    return {"success": True}


# ============================================
# EMAIL NOTIFICATIONS
# ============================================

@router.post("/email/send")
async def send_email_notification(
    email_data: EmailNotificationRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Send an email notification."""
    if EmailService is None:
        raise HTTPException(status_code=503, detail="Email service is not available")
    
    success = await EmailService.send_admin_notification(
        recipient=email_data.recipient,
        title=email_data.subject,
        message=email_data.message,
        notification_type=email_data.notification_type,
        db=db
    )
    
    if success:
        return {"success": True, "message": "Email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")


@router.get("/email/history", response_model=List[EmailNotificationResponse])
async def get_email_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get email notification history."""
    emails = db.query(EmailNotification).order_by(
        EmailNotification.created_at.desc()
    ).limit(limit).all()
    
    return emails


# ============================================
# API TOKENS
# ============================================

@router.get("/api-tokens", response_model=List[ApiTokenResponse])
async def list_api_tokens(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all API tokens."""
    tokens = db.query(ApiToken).all()
    return tokens


@router.delete("/api-tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Revoke an API token."""
    token = db.query(ApiToken).filter(ApiToken.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    db.delete(token)
    db.commit()
    
    logger.info(f"API token revoked: {token.name} by {current_admin.username}")
    return None


# ============================================
# EXPORT FUNCTIONALITY
# ============================================

@router.get("/export/analytics/csv")
async def export_analytics_csv(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Export analytics to CSV."""
    try:
        # Get comprehensive stats
        overall_stats = await get_overall_stats(db=db, current_admin=current_admin)
        daily_stats = await get_daily_stats(days=30, db=db, current_admin=current_admin)
        monthly_stats = await get_monthly_stats(months=12, db=db, current_admin=current_admin)
        
        stats_data = {
            **overall_stats.model_dump(),
            'daily_stats': [stat.model_dump() for stat in daily_stats],
            'monthly_stats': [stat.model_dump() for stat in monthly_stats]
        }
        
        # Export to CSV
        csv_file = ExportService.export_statistics_to_csv(stats_data)
        
        return StreamingResponse(
            csv_file,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    except Exception as e:
        logger.error(f"CSV export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/analytics/pdf")
async def export_analytics_pdf(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Export analytics to PDF."""
    try:
        # Get comprehensive stats
        overall_stats = await get_overall_stats(db=db, current_admin=current_admin)
        daily_stats = await get_daily_stats(days=30, db=db, current_admin=current_admin)
        monthly_stats = await get_monthly_stats(months=12, db=db, current_admin=current_admin)
        
        # Export to PDF
        pdf_file = ExportService.export_analytics_pdf(
            overall_stats=overall_stats.model_dump(),
            daily_stats=[stat.model_dump() for stat in daily_stats],
            monthly_stats=[stat.model_dump() for stat in monthly_stats]
        )
        
        return StreamingResponse(
            pdf_file,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d')}.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ============================================
# ADVANCED SEARCH & FILTERING
# ============================================

@router.post("/search/downloads")
async def search_downloads(
    filters: SearchFilters,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Search and filter download logs."""
    query = db.query(DownloadLog)
    
    # Apply filters
    if filters.query:
        query = query.filter(
            or_(
                DownloadLog.video_title.ilike(f"%{filters.query}%"),
                DownloadLog.video_url.ilike(f"%{filters.query}%")
            )
        )
    
    if filters.start_date:
        query = query.filter(DownloadLog.download_date >= filters.start_date)
    
    if filters.end_date:
        query = query.filter(DownloadLog.download_date <= filters.end_date)
    
    if filters.status:
        success = filters.status.lower() == "success"
        query = query.filter(DownloadLog.success == success)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    downloads = query.order_by(DownloadLog.created_at.desc()).offset(filters.offset).limit(filters.limit).all()
    
    return {
        "total": total,
        "results": downloads,
        "limit": filters.limit,
        "offset": filters.offset
    }


@router.post("/search/pages")
async def search_pages(
    filters: SearchFilters,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Search and filter pages."""
    query = db.query(Page)
    
    if filters.query:
        query = query.filter(
            or_(
                Page.title.ilike(f"%{filters.query}%"),
                Page.slug.ilike(f"%{filters.query}%"),
                Page.content.ilike(f"%{filters.query}%")
            )
        )
    
    if filters.status:
        published = filters.status.lower() == "published"
        query = query.filter(Page.is_published == published)
    
    total = query.count()
    pages = query.order_by(Page.updated_at.desc()).offset(filters.offset).limit(filters.limit).all()
    
    return {
        "total": total,
        "results": pages,
        "limit": filters.limit,
        "offset": filters.offset
    }


# ============================================
# NEWS MANAGEMENT
# ============================================

@router.get("/news", response_model=List[NewsResponse])
async def list_news(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all news items."""
    news_items = db.query(News).order_by(News.news_date.desc(), News.order).all()
    return news_items


@router.get("/news/{news_id}", response_model=NewsResponse)
async def get_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get a specific news item by ID."""
    news_item = db.query(News).filter(News.id == news_id).first()
    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")
    return news_item


@router.post("/news", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    news_data: NewsCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Create a new news item."""
    news_item = News(**news_data.model_dump())
    db.add(news_item)
    db.commit()
    db.refresh(news_item)
    
    logger.info(f"News item created: {news_item.title} by {current_admin.username}")
    return news_item


@router.put("/news/{news_id}", response_model=NewsResponse)
async def update_news(
    news_id: int,
    news_data: NewsUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update an existing news item."""
    news_item = db.query(News).filter(News.id == news_id).first()
    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")
    
    update_data = news_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(news_item, key, value)
    
    db.commit()
    db.refresh(news_item)
    
    logger.info(f"News item updated: {news_item.title} by {current_admin.username}")
    return news_item


@router.delete("/news/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete a news item."""
    news_item = db.query(News).filter(News.id == news_id).first()
    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")
    
    title = news_item.title
    db.delete(news_item)
    db.commit()
    
    logger.info(f"News item deleted: {title} by {current_admin.username}")
    return None
