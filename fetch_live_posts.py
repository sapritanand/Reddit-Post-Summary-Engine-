import os
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

    print("Fetching top 5 hot posts from r/Python...\n")
    subreddit = reddit.subreddit('Python')
    for i, submission in enumerate(subreddit.hot(limit=5), 1):
        print(f"{i}. {submission.title}")
        print(f"   URL: https://reddit.com{submission.permalink}")
        print(f"   Score: {submission.score}, Comments: {submission.num_comments}")
        print()


if __name__ == "__main__":
    main()
