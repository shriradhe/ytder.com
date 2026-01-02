# SEO Management Guide

## Overview

The SEO Management system allows you to update SEO settings for your frontend website on a daily basis or on-demand from the admin panel.

## Features

- **Dynamic SEO Tags**: All meta tags are injected dynamically into the frontend
- **Complete SEO Support**: Meta tags, Open Graph, Twitter Cards, Canonical URLs
- **History Tracking**: View and track all SEO changes
- **Active/Inactive Toggle**: Test settings before going live
- **Real-time Updates**: Changes apply immediately to frontend

## Accessing SEO Settings

1. Log in to the Admin Panel
2. Navigate to **SEO Settings** in the sidebar
3. You'll see the SEO management form

## SEO Fields Explained

### Basic SEO

- **Page Title** (Required): Appears in browser tabs and search results
  - Recommended: 50-60 characters
  - Example: "Video Downloader - Download HD Videos from Any Platform"

- **Meta Description** (Required): Appears in search result snippets
  - Recommended: 150-160 characters
  - Example: "Download high-quality videos from YouTube, Instagram, TikTok, and more..."

- **Meta Keywords**: Comma-separated keywords
  - Example: "video downloader, youtube, instagram, tiktok"

- **Robots Meta**: Search engine directives
  - Default: "index, follow"
  - Options: "noindex, nofollow", "index, nofollow", etc.

### Open Graph (Facebook, LinkedIn)

- **OG Title**: Title for social media shares (defaults to page title)
- **OG Description**: Description for social media (defaults to meta description)
- **OG Image**: Image URL for social sharing (recommended: 1200x630px)
- **OG URL**: Canonical URL for the shared page

### Twitter Card

- **Twitter Card Type**: 
  - `summary`: Small card
  - `summary_large_image`: Large image card (recommended)
- **Twitter Title**: Title for Twitter shares
- **Twitter Description**: Description for Twitter
- **Twitter Image**: Image URL (recommended: 1200x600px)

### Canonical URL

- **Canonical URL**: Preferred URL for this page
- Helps prevent duplicate content issues
- Example: "https://example.com"

## How to Update SEO

### Daily Updates

1. Go to **SEO Settings** in admin panel
2. Update the fields you want to change
3. Click **Save SEO Settings**
4. Settings are applied immediately to the frontend

### On-Demand Updates

You can update SEO settings anytime:
- For special events or promotions
- To optimize for specific keywords
- To update social media previews
- To fix SEO issues

## Best Practices

### Page Title
- Keep it under 60 characters
- Include primary keyword
- Make it compelling and descriptive
- Unique for each page

### Meta Description
- Keep it under 160 characters
- Include call-to-action
- Use keywords naturally
- Make it compelling

### Images
- Use high-quality images (1200x630px for OG, 1200x600px for Twitter)
- Optimize file size
- Use absolute URLs
- Include alt text in images

### Keywords
- Focus on 3-5 primary keywords
- Use long-tail keywords
- Research competitor keywords
- Update based on analytics

## Viewing History

1. Click **View History** button in SEO Settings
2. See all past SEO configurations
3. Track when changes were made
4. Identify active vs inactive settings

## Testing SEO Changes

1. Update SEO settings
2. Set **Active** checkbox to unchecked
3. Save settings
4. Test on frontend
5. When satisfied, check **Active** and save

## Frontend Integration

SEO tags are automatically injected into the frontend HTML:
- Meta tags are added to `<head>` section
- Title tag is updated
- Open Graph tags for social sharing
- Twitter Card tags for Twitter
- Canonical URL for SEO

## API Endpoints

### Admin Endpoints (Requires Authentication)

- `GET /api/admin/seo` - Get current SEO settings
- `POST /api/admin/seo` - Create/update SEO settings
- `PUT /api/admin/seo/{id}` - Update specific SEO settings
- `GET /api/admin/seo/history` - View SEO history

### Public Endpoint

- `GET /api/seo` - Get active SEO settings (for frontend)

## Troubleshooting

### SEO Tags Not Appearing

1. Check if SEO settings are marked as **Active**
2. Clear browser cache
3. Check server logs for errors
4. Verify database connection

### Changes Not Reflecting

1. Ensure you clicked **Save SEO Settings**
2. Check if settings are active
3. Restart server if needed
4. Clear browser cache

## Tips

- Update SEO regularly based on analytics
- Test changes before making them active
- Use history to track what works
- Monitor search engine rankings
- Update for seasonal campaigns

---

**Last Updated**: December 29, 2025

