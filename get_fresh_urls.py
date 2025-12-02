"""
Utility script to fetch current popular Reddit posts for analysis testing.
Helps avoid stale/deleted URLs by providing fresh, active post URLs.
"""

import os
import sys
import praw
from dotenv import load_dotenv


def get_hot_posts(subreddit_name: str, limit: int = 5):
    """Fetch hot posts from specified subreddit"""
    load_dotenv()
    
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT', 'RedditAnalyzer/1.0')
    )
    
    print(f"\n🔥 Fetching top {limit} hot posts from r/{subreddit_name}...\n")
    print("="*80)
    
    subreddit = reddit.subreddit(subreddit_name)
    posts = []
    
    for i, submission in enumerate(subreddit.hot(limit=limit), 1):
        url = f"https://reddit.com{submission.permalink}"
        posts.append({
            'number': i,
            'title': submission.title,
            'url': url,
            'score': submission.score,
            'comments': submission.num_comments
        })
        
        print(f"\n{i}. {submission.title}")
        print(f"   📊 Score: {submission.score} | 💬 Comments: {submission.num_comments}")
        print(f"   🔗 URL: {url}")
    
    print("\n" + "="*80)
    print("\n✨ To analyze a post, run:")
    print("   python cli.py analyze \"<URL>\"")
    print("\nExample:")
    if posts:
        print(f'   python cli.py analyze "{posts[0]["url"]}"')
    
    return posts


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        subreddit = sys.argv[1]
    else:
        subreddit = 'Python'
    
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    try:
        get_hot_posts(subreddit, limit)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nUsage:")
        print("  python get_fresh_urls.py [subreddit] [limit]")
        print("\nExamples:")
        print("  python get_fresh_urls.py Python 10")
        print("  python get_fresh_urls.py AskReddit 5")
        print("  python get_fresh_urls.py technology")


if __name__ == "__main__":
    main()
