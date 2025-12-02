"""
Quick Start Script - Simple example to get started quickly
"""

import os
from pathlib import Path

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file created!")
        print("⚠️  Please edit .env file and add your API credentials")
        return False
    elif not env_file.exists():
        print("❌ .env.example not found!")
        return False
    
    return True


def check_credentials():
    """Check if credentials are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    reddit_id = os.getenv('REDDIT_CLIENT_ID')
    reddit_secret = os.getenv('REDDIT_CLIENT_SECRET')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    missing = []
    if not reddit_id or reddit_id == 'your_client_id_here':
        missing.append('REDDIT_CLIENT_ID')
    if not reddit_secret or reddit_secret == 'your_client_secret_here':
        missing.append('REDDIT_CLIENT_SECRET')
    if not gemini_key or gemini_key == 'your_gemini_api_key_here':
        missing.append('GEMINI_API_KEY')
    
    if missing:
        print("❌ Missing or invalid credentials:")
        for cred in missing:
            print(f"   - {cred}")
        print("\n📝 Please edit .env file and add your credentials")
        print("\nHow to get credentials:")
        print("  Reddit: https://www.reddit.com/prefs/apps")
        print("  Gemini: https://makersuite.google.com/app/apikey")
        return False
    
    print("✅ Credentials found!")
    return True


def quick_test():
    """Run a quick test"""
    print("\n" + "="*60)
    print("QUICK TEST")
    print("="*60 + "\n")
    
    try:
        from reddit_analyzer import RedditAnalyzer
        
        print("Initializing analyzer...")
        analyzer = RedditAnalyzer.from_env()
        
        print("✅ Analyzer initialized successfully!")
        
        # Test cache
        stats = analyzer.get_cache_stats()
        print(f"\n📦 Cache stats: {stats}")
        
        print("\n✨ System is ready to use!")
        print("\nTo analyze a post, run:")
        print('  python cli.py analyze "POST_URL"')
        print("\nOr use the examples:")
        print('  python examples.py')
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check:")
        print("  1. All dependencies are installed (pip install -r requirements.txt)")
        print("  2. Credentials in .env are correct")
        print("  3. You have internet connection")
        return False


def main():
    """Main quick start function"""
    print("\n" + "="*60)
    print(" "*15 + "REDDIT ANALYSIS SYSTEM")
    print(" "*20 + "Quick Start")
    print("="*60 + "\n")
    
    # Step 1: Create .env if needed
    print("Step 1: Checking environment file...")
    if not create_env_file():
        return
    
    # Step 2: Check credentials
    print("\nStep 2: Checking credentials...")
    if not check_credentials():
        return
    
    # Step 3: Quick test
    print("\nStep 3: Testing system...")
    if not quick_test():
        return
    
    print("\n" + "="*60)
    print("✨ QUICK START COMPLETE!")
    print("="*60)


if __name__ == '__main__':
    main()
