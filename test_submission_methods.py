import os
import sys
import praw
from dotenv import load_dotenv


def main():
    load_dotenv()
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'RedditAnalyzer/Debug')

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = "https://www.reddit.com/r/Python/comments/1h4l0zd/what_do_you_automate_with_python/"

    print(f"\n=== METHOD 1: submission(url=...) ===")
    try:
        sub1 = reddit.submission(url=test_url)
        print(f"ID: {sub1.id}")
        print(f"Title: {sub1.title}")
        print(f"Subreddit: {sub1.subreddit.display_name}")
        print(f"Score: {sub1.score}")
    except Exception as e:
        print(f"Failed: {e}")

    # Extract ID
    if '/comments/' in test_url:
        post_id = test_url.split('/comments/')[1].split('/')[0]
    else:
        post_id = None

    if post_id:
        print(f"\n=== METHOD 2: submission(id={post_id}) ===")
        try:
            sub2 = reddit.submission(id=post_id)
            print(f"ID: {sub2.id}")
            print(f"Title: {sub2.title}")
            print(f"Subreddit: {sub2.subreddit.display_name}")
            print(f"Score: {sub2.score}")
        except Exception as e:
            print(f"Failed: {e}")

    print("\nConclusion: Compare which method gives the correct post.")


if __name__ == "__main__":
    main()
