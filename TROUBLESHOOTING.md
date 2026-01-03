# Troubleshooting Guide

## Common Errors and Solutions

### 1. Python 3.9 Deprecation Warning

**Error:**
```
Deprecated Feature: Support for Python version 3.9 has been deprecated. Please update to Python 3.10 or above
```

**Solution:**
1. Ensure `runtime.txt` contains: `python-3.11.0`
2. On Render.com, trigger a manual deployment:
   - Go to Render dashboard → Your service → Manual Deploy → Clear build cache & deploy
3. Verify Python version in build logs

### 2. DNS/Network Error: "No address associated with hostname"

**Error:**
```
ERROR: [youtube] VIDEO_ID: Unable to download API page: [Errno -5] No address associated with hostname
```

**Possible Causes:**

#### A. Invalid Proxy Configuration
If you have `PROXY` environment variable set, it might be invalid.

**Check:**
1. Go to Render dashboard → Environment
2. Check if `PROXY` variable exists
3. Verify proxy URL format is correct:
   - ✅ `http://proxy.example.com:8080`
   - ✅ `socks5://proxy.example.com:1080`
   - ✅ `http://user:pass@proxy.example.com:8080`
   - ❌ `proxy.example.com:8080` (missing protocol)
   - ❌ `http://invalid-host-that-doesnt-exist.com:8080`

**Solution:**
- **Option 1:** Remove/delete `PROXY` environment variable if you don't need it
- **Option 2:** Fix the proxy URL to a valid, accessible proxy server
- **Option 3:** Test proxy connectivity first:
  ```bash
  curl -x http://your-proxy:port https://www.google.com
  ```

#### B. Proxy Server Unreachable
Even if proxy URL format is correct, the proxy server might be:
- Down/offline
- Blocking requests
- Not accessible from Render's network

**Solution:**
- Test proxy from another location
- Try a different proxy server
- Remove proxy if not essential

#### C. Network Connectivity Issue (Rare)
Render's network might have connectivity issues.

**Solution:**
- Wait a few minutes and retry
- Check Render status page
- Contact Render support if persistent

### 3. Quick Fix Steps

**For Render.com Deployment:**

1. **Check Environment Variables:**
   ```
   Render Dashboard → Your Service → Environment
   ```
   - Look for `PROXY` variable
   - If it exists and you don't need it → Delete it
   - If you need it → Verify it's correct

2. **Clear Build Cache and Redeploy:**
   ```
   Render Dashboard → Your Service → Manual Deploy → Clear build cache & deploy
   ```

3. **Check Build Logs:**
   - Verify Python version shows 3.11+
   - Check for any proxy-related warnings

4. **Check Runtime Logs:**
   - Look for proxy initialization messages
   - Check for DNS/network errors

### 4. Testing Without Proxy

If you're experiencing DNS errors:

1. **Remove Proxy:**
   - Go to Render Environment settings
   - Delete `PROXY` variable
   - Redeploy service

2. **Test again:**
   - The service should work without proxy
   - Proxy is optional - only needed for geo-blocking

### 5. Proxy Validation

Before setting `PROXY` environment variable:

1. **Test proxy connectivity:**
   ```bash
   curl -x http://proxy-host:port https://www.google.com
   ```

2. **Verify proxy works with yt-dlp:**
   ```bash
   yt-dlp --proxy http://proxy-host:port "https://www.youtube.com/watch?v=TEST"
   ```

3. **Only set PROXY if:**
   - Proxy is accessible
   - Proxy responds to test requests
   - You actually need geo-blocking bypass

### 6. Environment Variables Checklist

**Required (Auto-set by Render):**
- `PORT` - Set by Render automatically
- `HOST` - Optional, defaults to 0.0.0.0

**Optional:**
- `PROXY` - Only set if you have a valid, working proxy
- `COOKIES_FILE` - Only set if you have a cookies.txt file
- `MAX_CONCURRENT_DOWNLOADS` - Optional performance tuning
- `CACHE_TTL_SECONDS` - Optional cache tuning
- `RATE_LIMIT_PER_MINUTE` - Optional rate limiting

**Recommendation:**
- Start with minimal configuration
- Add `PROXY` only if needed
- Test each addition separately

## Getting Help

If issues persist:

1. Check Render service logs for detailed error messages
2. Verify all environment variables are correct
3. Test with minimal configuration first
4. Check Render status page for service issues
5. Review application logs in Render dashboard

