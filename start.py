"""Quick start script for the video download service."""
import subprocess
import sys
import os


def check_dependencies():
    """Check if yt-dlp is installed."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ yt-dlp is installed: {result.stdout.strip()}")
            return True
        else:
            print("✗ yt-dlp is not working properly")
            return False
    except FileNotFoundError:
        print("✗ yt-dlp is not installed")
        print("  Install with: pip install yt-dlp")
        return False
    except Exception as e:
        print(f"✗ Error checking yt-dlp: {e}")
        return False


def check_python_packages():
    """Check if required Python packages are installed."""
    required = ["fastapi", "uvicorn", "pydantic", "cachetools"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is not installed")
            missing.append(package)
    
    if missing:
        print("\nInstall missing packages with:")
        print("  pip install -r requirements.txt")
        return False
    return True


def create_static_dir():
    """Ensure static directory exists."""
    if not os.path.exists("static"):
        os.makedirs("static")
        print("✓ Created static directory")
    else:
        print("✓ Static directory exists")


def main():
    """Run startup checks and launch the server."""
    print("=" * 60)
    print("Video Download Service - Startup Check")
    print("=" * 60)
    print()
    
    # Check dependencies
    deps_ok = check_dependencies()
    packages_ok = check_python_packages()
    create_static_dir()
    
    print()
    
    if not (deps_ok and packages_ok):
        print("❌ Prerequisites not met. Please install missing dependencies.")
        sys.exit(1)
    
    print("=" * 60)
    print("✅ All checks passed! Starting server...")
    print("=" * 60)
    print()
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("❤️  Health check at: http://localhost:8000/api/health")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # Start the server
    try:
        subprocess.run([
            "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")


if __name__ == "__main__":
    main()

