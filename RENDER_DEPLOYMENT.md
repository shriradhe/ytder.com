# 🚀 Render.com Deployment Guide

This guide will help you deploy the ytder video downloader to Render.com.

## 📋 Prerequisites

1. A GitHub account
2. Your code pushed to a GitHub repository
3. A Render.com account (free tier available)

## 🔧 Deployment Steps

### Option 1: Using render.yaml (Recommended)

1. **Push your code to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Configure for Render.com deployment"
   git push origin main
   ```

2. **Go to Render.com Dashboard**
   - Visit https://dashboard.render.com
   - Click "New +" → "Blueprint"

3. **Connect your GitHub repository**
   - Select your repository
   - Render will automatically detect `render.yaml`

4. **Review and Deploy**
   - Render will use the configuration from `render.yaml`
   - Click "Apply" to deploy

### Option 2: Manual Setup

1. **Go to Render.com Dashboard**
   - Visit https://dashboard.render.com
   - Click "New +" → "Web Service"

2. **Connect your GitHub repository**
   - Select your repository
   - Choose the branch (usually `main` or `master`)

3. **Configure the service:**
   - **Name**: `ytder-video-downloader` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Choose Starter (free) or Standard/Pro for production

4. **Environment Variables** (optional, defaults are fine):
   - `HOST`: `0.0.0.0` (already set in config)
   - `PORT`: Automatically set by Render (don't override)
   - `MAX_CONCURRENT_DOWNLOADS`: `10` (optional)
   - `CACHE_TTL_SECONDS`: `3600` (optional)
   - `RATE_LIMIT_PER_MINUTE`: `30` (optional)

5. **Health Check Path**: `/api/health`

6. **Click "Create Web Service"**

## ⚙️ Configuration Files

The following files are configured for Render:

- **`render.yaml`**: Blueprint configuration (auto-deployment)
- **`Procfile`**: Process file for Render
- **`runtime.txt`**: Python version specification
- **`src/config.py`**: Updated to use `PORT` from environment

## 🗄️ Database Considerations

### Current Setup (SQLite)
- The app uses SQLite by default
- **⚠️ Important**: Render's free tier uses ephemeral file systems
- **Data will be lost on service restart** with SQLite

### Recommended: Use PostgreSQL (Production)

For production, use Render's PostgreSQL service:

1. **Create a PostgreSQL Database:**
   - In Render dashboard: "New +" → "PostgreSQL"
   - Choose a name and plan
   - Copy the **Internal Database URL**

2. **Update Environment Variable:**
   - In your Web Service settings
   - Add: `DATABASE_URL` = (your PostgreSQL connection string)
   - Format: `postgresql://user:password@host:port/dbname`

3. **Update requirements.txt** (if needed):
   ```txt
   psycopg2-binary>=2.9.0
   ```

The app will automatically use PostgreSQL if `DATABASE_URL` is set.

## 🔍 Health Check

The service includes a health check endpoint:
- **URL**: `https://your-app.onrender.com/api/health`
- Render will use this to monitor your service

## 📝 Environment Variables

You can set these in Render's dashboard under "Environment":

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host (don't change) |
| `PORT` | Auto-set | Server port (don't override) |
| `DATABASE_URL` | SQLite | Database connection string |
| `MAX_CONCURRENT_DOWNLOADS` | `10` | Max parallel downloads |
| `CACHE_TTL_SECONDS` | `3600` | Cache expiration time |
| `RATE_LIMIT_PER_MINUTE` | `30` | Rate limit per IP |

## 🚨 Important Notes

1. **Free Tier Limitations:**
   - Services spin down after 15 minutes of inactivity
   - First request after spin-down takes ~30-50 seconds
   - Consider upgrading to Standard plan for always-on service

2. **File System:**
   - Ephemeral - files are lost on restart
   - Use external storage (S3, etc.) for persistent files
   - Database should use PostgreSQL for persistence

3. **yt-dlp Requirements:**
   - yt-dlp is installed via pip (included in requirements.txt)
   - FFmpeg may be needed for video merging
   - Render doesn't include FFmpeg by default - you may need a build script

4. **Build Time:**
   - First deployment takes 5-10 minutes
   - Subsequent deployments are faster

## 🔧 Troubleshooting

### Service won't start
- Check logs in Render dashboard
- Verify `requirements.txt` is correct
- Ensure `main:app` is the correct module path

### Database errors
- Verify `DATABASE_URL` is set correctly
- For PostgreSQL, ensure database is created and accessible
- Check connection string format

### Timeout errors
- Increase timeout in Render service settings
- Check `YTDLP_TIMEOUT_SECONDS` environment variable

### yt-dlp not found
- Verify yt-dlp is in requirements.txt
- Check build logs for installation errors

## 📚 Additional Resources

- [Render.com Documentation](https://render.com/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Python on Render](https://render.com/docs/python)

## ✅ Post-Deployment Checklist

- [ ] Service is running and healthy
- [ ] Health check endpoint responds
- [ ] Test video download functionality
- [ ] Database is accessible (if using PostgreSQL)
- [ ] Admin panel is accessible
- [ ] Environment variables are set correctly
- [ ] Custom domain configured (if needed)

---

**Need Help?** Check the logs in Render dashboard or review the application logs for detailed error messages.

