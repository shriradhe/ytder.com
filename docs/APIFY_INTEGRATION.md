# Apify API Integration

This document explains how to configure and use Apify API as a fallback when yt-dlp fails to extract YouTube videos.

## Overview

Apify is a web scraping and automation platform that provides cloud-based actors (scripts) for extracting data from websites. When yt-dlp fails to extract YouTube videos (due to IP blocking, API changes, etc.), the service can automatically fall back to Apify's YouTube scraper.

## How It Works

1. **Primary Method**: yt-dlp tries to extract video information
2. **Fallback**: If all yt-dlp player clients fail, Apify API is used automatically
3. **Seamless**: The response format is identical, so users don't notice the difference

## Setup

### 1. Create Apify Account

1. Go to [Apify.com](https://apify.com) and create a free account
2. Navigate to [Account Settings → Integrations](https://console.apify.com/account/integrations)
3. Copy your **API Token**

### 2. Choose an Actor

Apify provides several YouTube scraping actors:

#### Recommended: `apify/youtube-scraper`
- Official Apify actor
- Well-maintained and updated
- Good for extracting video metadata and formats

#### Alternative: `bluepenguins455/yt-downloader`
- Uses yt-dlp under the hood
- Can download videos directly
- Good for download links

### 3. Configure Environment Variables

Add these to your Render.com environment or `.env` file:

```bash
# Enable Apify fallback
APIFY_ENABLED=true

# Your Apify API token (required)
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Actor ID (optional, defaults to apify/youtube-scraper)
APIFY_ACTOR_ID=apify/youtube-scraper

# Timeout in seconds (optional, defaults to 120)
APIFY_TIMEOUT_SECONDS=120
```

### 4. For Render.com Deployment

1. Go to Render dashboard → Your service → **Environment**
2. Add environment variables:
   - **Key**: `APIFY_ENABLED` → **Value**: `true`
   - **Key**: `APIFY_API_TOKEN` → **Value**: `your-api-token-here`
   - **Key**: `APIFY_ACTOR_ID` → **Value**: `apify/youtube-scraper` (optional)
3. Save and redeploy

## Cost Considerations

### Apify Free Tier
- **$5 free credits** per month
- Each actor run costs credits (varies by actor)
- YouTube scraper typically costs ~$0.01-0.05 per video

### Usage Tips
- Apify is only used as a **fallback** when yt-dlp fails
- Most videos will still use yt-dlp (free)
- Only problematic videos use Apify (costs credits)
- Monitor usage in [Apify Console](https://console.apify.com/account/usage)

## How It Works Technically

### Request Flow

```
1. User requests YouTube video
   ↓
2. yt-dlp tries extraction (ios, android, web, mweb clients)
   ↓
3. If all yt-dlp clients fail:
   ↓
4. Apify API is called automatically
   ↓
5. Apify actor extracts video info
   ↓
6. Results are processed and returned
```

### Code Flow

1. **yt-dlp attempts** (primary method)
   - Tries all player clients
   - Fast and free
   - Works for most videos

2. **Apify fallback** (if yt-dlp fails)
   - Only triggered when all yt-dlp clients fail
   - Uses cloud-based scraping
   - Bypasses IP blocking
   - Costs Apify credits

## Supported Actors

### `apify/youtube-scraper` (Default)

**Input:**
```json
{
  "startUrls": [{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}],
  "maxVideos": 1
}
```

**Output:**
- Video title, description, thumbnail
- View count, duration, uploader
- Format information
- Download URLs

### `bluepenguins455/yt-downloader`

**Input:**
```json
{
  "videoUrls": ["https://www.youtube.com/watch?v=VIDEO_ID"],
  "quality": "best"
}
```

**Output:**
- Direct download links
- Video metadata
- Format options

## Monitoring

### Check Logs

When Apify is used, you'll see:
```
INFO - All player clients failed. Last error: ...
INFO - Attempting Apify API as fallback...
INFO - Successfully extracted video info using Apify API
```

### Apify Console

Monitor usage at:
- [Apify Console → Usage](https://console.apify.com/account/usage)
- Track credit consumption
- View actor run history

## Troubleshooting

### Apify Not Being Used

**Check:**
1. `APIFY_ENABLED=true` is set
2. `APIFY_API_TOKEN` is valid
3. Check logs for "Apify client enabled" message

**Logs to check:**
```
INFO - Apify client enabled with actor: apify/youtube-scraper
```

### Apify API Errors

**Common errors:**
- `401 Unauthorized` → Invalid API token
- `404 Not Found` → Invalid actor ID
- `429 Too Many Requests` → Rate limit exceeded
- `Timeout` → Actor took too long

**Solutions:**
- Verify API token is correct
- Check actor ID is valid
- Increase `APIFY_TIMEOUT_SECONDS` if needed
- Check Apify account has credits

### Cost Management

**To limit costs:**
- Only enable Apify when needed
- Monitor usage regularly
- Set up Apify usage alerts
- Consider upgrading Apify plan if needed

## Best Practices

1. **Use Apify as Fallback Only**
   - yt-dlp is free and fast
   - Apify should only be used when yt-dlp fails

2. **Monitor Usage**
   - Check Apify console regularly
   - Set up usage alerts
   - Track credit consumption

3. **Combine with Other Solutions**
   - Use cookies for authentication
   - Use proxy for IP blocking
   - Apify as final fallback

4. **Test Before Production**
   - Test with a few videos first
   - Verify costs are acceptable
   - Monitor success rate

## Example Configuration

### Minimal (Free Tier)
```bash
APIFY_ENABLED=true
APIFY_API_TOKEN=your-token-here
# Uses default actor: apify/youtube-scraper
```

### Custom Actor
```bash
APIFY_ENABLED=true
APIFY_API_TOKEN=your-token-here
APIFY_ACTOR_ID=bluepenguins455/yt-downloader
APIFY_TIMEOUT_SECONDS=180
```

## Related Documentation

- [PROXY_AND_COOKIES.md](PROXY_AND_COOKIES.md) - Alternative solutions
- [YOUTUBE_EXTRACTION_ISSUES.md](YOUTUBE_EXTRACTION_ISSUES.md) - Troubleshooting YouTube issues
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - General troubleshooting

## Support

- [Apify Documentation](https://docs.apify.com/)
- [Apify YouTube Scraper](https://apify.com/apify/youtube-scraper)
- [Apify Support](https://apify.com/support)

