# Developer Guide

## Import Patterns

### From Root (main.py)
```python
from src.models import VideoRequest, VideoResponse
from src.service import VideoService
from src.config import settings
from src.database import get_db, Page
```

### Within src/ Package (Relative Imports)
```python
from .models import VideoRequest
from .service import VideoService
from .config import settings
from .database import get_db
```

## Adding New Modules

1. Create new file in `src/` directory
2. Use relative imports for other `src/` modules
3. Import from `src` in `main.py`
4. Update `PROJECT_SUMMARY.md` if adding major features

## Database Path

The database path is automatically resolved relative to the project root:
- Database location: `data/video_downloader.db`
- Backups: `data/backups/`
- Configure via `DATABASE_URL` environment variable

## Running the Application

### Development
```bash
python start.py          # With dependency checks
python main.py           # Direct start
uvicorn main:app --reload # With auto-reload
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Testing

Tests should be placed in `tests/` directory:
```python
# tests/test_service.py
from src.service import VideoService
# ... test code
```

Run with:
```bash
pytest tests/
```

## Code Style

- Follow PEP 8
- Use type hints where possible
- Document functions with docstrings
- Use relative imports within `src/`

## Project Structure Rules

1. **Source code** → `src/`
2. **Documentation** → `docs/`
3. **Data files** → `data/`
4. **Tests** → `tests/`
5. **Static files** → `static/`
6. **Entry point** → `main.py` (root level)

