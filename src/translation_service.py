"""Translation service for multi-language support."""
import json
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from .database import Translation

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for managing translations"""
    
    # Default translations (English)
    DEFAULT_TRANSLATIONS = {
        'en': {
            'app_title': 'Video Downloader',
            'paste_url': 'Paste video URL above',
            'detecting': 'Detecting video...',
            'download': 'Download',
            'formats_detected': 'formats detected!',
            'refresh_formats': 'Refresh formats',
            'highest_quality': 'Highest Quality',
            'lightning_fast': 'Lightning Fast',
            'multi_platform': 'Multi-Platform',
            'download_hd': 'Download videos in Full HD, 2K, and 4K with original audio quality',
            'instant_processing': 'Instant detection and processing. Cached videos load in under 1 second',
            'supports_platforms': 'Supports YouTube, Instagram, TikTok, Facebook, Twitter, Vimeo, and more',
            'admin_panel': 'Admin Panel',
            'dashboard': 'Dashboard',
            'pages': 'Pages',
            'home_sections': 'Home Sections',
            'analytics': 'Analytics',
            'settings': 'Settings',
            'logout': 'Logout',
            'total_downloads': 'Total Downloads',
            'total_page_views': 'Total Page Views',
            'today_downloads': "Today's Downloads",
            'this_month_downloads': 'This Month Downloads',
            'add_new_page': 'Add New Page',
            'add_new_section': 'Add New Section',
            'edit': 'Edit',
            'delete': 'Delete',
            'save': 'Save',
            'cancel': 'Cancel',
            'published': 'Published',
            'draft': 'Draft',
            'active': 'Active',
            'inactive': 'Inactive',
            'change_password': 'Change Password',
            'backup_database': 'Backup Database',
            'old_password': 'Old Password',
            'new_password': 'New Password',
            'update_password': 'Update Password',
            'create_backup': 'Create Backup Now',
            'email_notifications': 'Email Notifications',
            'language': 'Language',
            'theme': 'Theme',
        },
        'es': {  # Spanish
            'app_title': 'Descargador de Videos',
            'paste_url': 'Pegar URL del video arriba',
            'detecting': 'Detectando video...',
            'download': 'Descargar',
            'formats_detected': 'formatos detectados!',
            'refresh_formats': 'Actualizar formatos',
            'highest_quality': 'Máxima Calidad',
            'lightning_fast': 'Súper Rápido',
            'multi_platform': 'Multi-Plataforma',
            'admin_panel': 'Panel de Admin',
            'dashboard': 'Panel de Control',
            'pages': 'Páginas',
            'home_sections': 'Secciones de Inicio',
            'analytics': 'Analíticas',
            'settings': 'Configuración',
            'logout': 'Cerrar Sesión',
            'total_downloads': 'Total de Descargas',
            'total_page_views': 'Total de Vistas',
            'today_downloads': 'Descargas de Hoy',
            'this_month_downloads': 'Descargas del Mes',
        },
        'fr': {  # French
            'app_title': 'Téléchargeur de Vidéos',
            'paste_url': 'Coller l\'URL de la vidéo ci-dessus',
            'detecting': 'Détection de la vidéo...',
            'download': 'Télécharger',
            'formats_detected': 'formats détectés!',
            'refresh_formats': 'Actualiser les formats',
            'highest_quality': 'Qualité Maximale',
            'lightning_fast': 'Ultra Rapide',
            'multi_platform': 'Multi-Plateforme',
            'admin_panel': 'Panneau d\'Administration',
            'dashboard': 'Tableau de Bord',
            'pages': 'Pages',
            'home_sections': 'Sections d\'Accueil',
            'analytics': 'Analytiques',
            'settings': 'Paramètres',
            'logout': 'Déconnexion',
        },
        'de': {  # German
            'app_title': 'Video-Downloader',
            'paste_url': 'Video-URL oben einfügen',
            'detecting': 'Video wird erkannt...',
            'download': 'Herunterladen',
            'formats_detected': 'Formate erkannt!',
            'refresh_formats': 'Formate aktualisieren',
            'highest_quality': 'Höchste Qualität',
            'lightning_fast': 'Blitzschnell',
            'multi_platform': 'Multi-Plattform',
            'admin_panel': 'Admin-Panel',
            'dashboard': 'Dashboard',
            'pages': 'Seiten',
            'home_sections': 'Startseiten-Bereiche',
            'analytics': 'Analytik',
            'settings': 'Einstellungen',
            'logout': 'Abmelden',
        },
        'ar': {  # Arabic
            'app_title': 'محمل الفيديو',
            'paste_url': 'الصق رابط الفيديو أعلاه',
            'detecting': 'جاري اكتشاف الفيديو...',
            'download': 'تحميل',
            'formats_detected': 'تنسيقات تم اكتشافها!',
            'refresh_formats': 'تحديث التنسيقات',
            'highest_quality': 'أعلى جودة',
            'lightning_fast': 'سريع للغاية',
            'multi_platform': 'متعدد المنصات',
            'admin_panel': 'لوحة الإدارة',
            'dashboard': 'لوحة التحكم',
            'pages': 'الصفحات',
            'home_sections': 'أقسام الصفحة الرئيسية',
            'analytics': 'التحليلات',
            'settings': 'الإعدادات',
            'logout': 'تسجيل الخروج',
        },
        'hi': {  # Hindi
            'app_title': 'वीडियो डाउनलोडर',
            'paste_url': 'ऊपर वीडियो URL पेस्ट करें',
            'detecting': 'वीडियो का पता लगाया जा रहा है...',
            'download': 'डाउनलोड',
            'formats_detected': 'प्रारूप पाए गए!',
            'refresh_formats': 'प्रारूप रीफ्रेश करें',
            'highest_quality': 'उच्चतम गुणवत्ता',
            'lightning_fast': 'बिजली की तेजी',
            'multi_platform': 'मल्टी-प्लेटफॉर्म',
            'admin_panel': 'प्रशासन पैनल',
            'dashboard': 'डैशबोर्ड',
            'pages': 'पृष्ठ',
            'home_sections': 'होम अनुभाग',
            'analytics': 'विश्लेषण',
            'settings': 'सेटिंग्स',
            'logout': 'लॉगआउट',
        }
    }
    
    # Cache for loaded translations
    _cache: Dict[str, Dict[str, str]] = {}
    
    @classmethod
    def get_translation(
        cls,
        key: str,
        language: str = 'en',
        db: Optional[Session] = None
    ) -> str:
        """
        Get translation for a key in specified language.
        
        Args:
            key: Translation key
            language: Language code (e.g., 'en', 'es', 'fr')
            db: Database session (optional)
            
        Returns:
            Translated string or key if not found
        """
        # Try cache first
        if language in cls._cache and key in cls._cache[language]:
            return cls._cache[language][key]
        
        # Try database
        if db:
            translation = db.query(Translation).filter(
                Translation.language_code == language,
                Translation.key == key
            ).first()
            
            if translation:
                # Cache it
                if language not in cls._cache:
                    cls._cache[language] = {}
                cls._cache[language][key] = translation.value
                return translation.value
        
        # Try default translations
        if language in cls.DEFAULT_TRANSLATIONS:
            if key in cls.DEFAULT_TRANSLATIONS[language]:
                return cls.DEFAULT_TRANSLATIONS[language][key]
        
        # Fallback to English
        if key in cls.DEFAULT_TRANSLATIONS['en']:
            return cls.DEFAULT_TRANSLATIONS['en'][key]
        
        # Return key itself if nothing found
        return key
    
    @classmethod
    def get_translations(
        cls,
        language: str = 'en',
        db: Optional[Session] = None
    ) -> Dict[str, str]:
        """
        Get all translations for a language.
        
        Args:
            language: Language code
            db: Database session (optional)
            
        Returns:
            Dictionary of translations
        """
        # Start with default translations
        translations = cls.DEFAULT_TRANSLATIONS.get(language, {}).copy()
        
        # Add English as fallback
        if language != 'en':
            translations.update(cls.DEFAULT_TRANSLATIONS['en'])
        
        # Override with database translations
        if db:
            db_translations = db.query(Translation).filter(
                Translation.language_code == language
            ).all()
            
            for trans in db_translations:
                translations[trans.key] = trans.value
        
        return translations
    
    @classmethod
    def save_translation(
        cls,
        language: str,
        key: str,
        value: str,
        db: Session
    ) -> bool:
        """
        Save or update a translation.
        
        Args:
            language: Language code
            key: Translation key
            value: Translation value
            db: Database session
            
        Returns:
            Success status
        """
        try:
            # Check if exists
            translation = db.query(Translation).filter(
                Translation.language_code == language,
                Translation.key == key
            ).first()
            
            if translation:
                translation.value = value
            else:
                translation = Translation(
                    language_code=language,
                    key=key,
                    value=value
                )
                db.add(translation)
            
            db.commit()
            
            # Update cache
            if language not in cls._cache:
                cls._cache[language] = {}
            cls._cache[language][key] = value
            
            return True
        except Exception as e:
            logger.error(f"Failed to save translation: {str(e)}")
            db.rollback()
            return False
    
    @classmethod
    def get_available_languages(cls) -> List[Dict[str, str]]:
        """Get list of available languages."""
        return [
            {'code': 'en', 'name': 'English', 'native_name': 'English'},
            {'code': 'es', 'name': 'Spanish', 'native_name': 'Español'},
            {'code': 'fr', 'name': 'French', 'native_name': 'Français'},
            {'code': 'de', 'name': 'German', 'native_name': 'Deutsch'},
            {'code': 'ar', 'name': 'Arabic', 'native_name': 'العربية'},
            {'code': 'hi', 'name': 'Hindi', 'native_name': 'हिन्दी'},
            {'code': 'zh', 'name': 'Chinese', 'native_name': '中文'},
            {'code': 'ja', 'name': 'Japanese', 'native_name': '日本語'},
            {'code': 'pt', 'name': 'Portuguese', 'native_name': 'Português'},
            {'code': 'ru', 'name': 'Russian', 'native_name': 'Русский'},
        ]
    
    @classmethod
    def clear_cache(cls):
        """Clear translation cache."""
        cls._cache = {}
    
    @classmethod
    def initialize_default_translations(cls, db: Session):
        """Initialize database with default translations."""
        try:
            for lang_code, translations in cls.DEFAULT_TRANSLATIONS.items():
                for key, value in translations.items():
                    existing = db.query(Translation).filter(
                        Translation.language_code == lang_code,
                        Translation.key == key
                    ).first()
                    
                    if not existing:
                        translation = Translation(
                            language_code=lang_code,
                            key=key,
                            value=value
                        )
                        db.add(translation)
            
            db.commit()
            logger.info("Default translations initialized")
        except Exception as e:
            logger.error(f"Failed to initialize translations: {str(e)}")
            db.rollback()

