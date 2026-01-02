#!/bin/bash
# Build script for Render.com deployment
# This script installs dependencies and sets up the environment

set -e  # Exit on error

echo "🔧 Building ytder video downloader..."

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Note: FFmpeg is not included by default on Render
# If you need FFmpeg for video merging, you'll need to:
# 1. Use a Docker image with FFmpeg pre-installed, OR
# 2. Install FFmpeg in the build script (may require custom Docker image)
# 3. Use Render's native buildpacks (limited FFmpeg support)

# Check if yt-dlp is installed
echo "✅ Checking yt-dlp installation..."
yt-dlp --version || echo "⚠️ Warning: yt-dlp not found in PATH"

echo "✅ Build complete!"

