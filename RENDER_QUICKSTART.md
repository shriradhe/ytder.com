# 🚀 Render.com Quick Start

## Quick Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Configure for Render"
   git push
   ```

2. **Deploy on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repo
   - Click "Apply"

That's it! Render will use `render.yaml` for configuration.

## What's Configured

✅ **Host & Port**: Automatically uses `0.0.0.0` and `$PORT`  
✅ **Health Check**: `/api/health`  
✅ **Python Version**: 3.11.0  
✅ **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Important Notes

⚠️ **Free Tier**: Services spin down after 15 min inactivity  
⚠️ **SQLite**: Data lost on restart (use PostgreSQL for production)  
⚠️ **FFmpeg**: Not included by default (needed for video merging)

## Optional: PostgreSQL Database

1. Create PostgreSQL service in Render
2. Add to `render.yaml`:
   ```yaml
   - key: DATABASE_URL
     fromDatabase:
       name: your-db-name
       property: connectionString
   ```
3. Uncomment `psycopg2-binary` in `requirements.txt`

## Files Created

- `render.yaml` - Render blueprint configuration
- `Procfile` - Process file
- `runtime.txt` - Python version
- `build.sh` - Build script (optional)
- `RENDER_DEPLOYMENT.md` - Full deployment guide

See `RENDER_DEPLOYMENT.md` for detailed instructions.

