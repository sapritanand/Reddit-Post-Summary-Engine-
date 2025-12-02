import os
import sys
import praw
from dotenv import load_dotenv


def extract_post_id(url: str) -> str:
    try:
        if '/comments/' in url:
            return url.split('/comments/')[1].split('/')[0]
        if 'redd.it' in url:
            return url.rstrip('/').split('/')[-1]
    except Exception:
        return ''
    return ''


def main():
    load_dotenv()
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'RedditAnalyzer/Debug')

    if not (client_id and client_secret and user_agent):
        print('Missing Reddit credentials in .env')
        sys.exit(1)

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = "https://www.reddit.com/r/Python/comments/1h4l0zd/what_do_you_automate_with_python/"

    post_id = extract_post_id(test_url)
    print(f"Extracted post ID: {post_id}")

    submission = reddit.submission(id=post_id) if post_id else reddit.submission(url=test_url)

    print("\nFetched post details:")
    print(f"  ID: {submission.id}")
    print(f"  Title: {submission.title}")
    print(f"  Subreddit: {submission.subreddit.display_name}")
    print(f"  Score: {submission.score}")
    print(f"  Num comments (meta): {submission.num_comments}")
    body_preview = (submission.selftext or '')[:120]
    print(f"  Body (first 120 chars): {body_preview}")

    # Validate title keywords vs URL slug
    slug = test_url.split('/comments/')[1].split('/')[1] if '/comments/' in test_url else ''
    slug_keywords = [w for w in slug.split('-') if len(w) >= 4]
    fetched_title = (submission.title or '').lower()
    ok = any(k in fetched_title for k in slug_keywords) if slug_keywords else True
    print("\nValidation:")
    print("  Slug keywords:", slug_keywords)
    print("  Fetched title:", fetched_title)
    print("  Match:", "YES" if ok else "NO")

    # Fetch comments
    submission.comments.replace_more(limit=0)
    all_comments = list(submission.comments.list())
    print(f"\nComment details:")
    print(f"  Total comments (flattened): {len(all_comments)}")
    if len(all_comments) > 0:
        top_comment = max(all_comments, key=lambda c: getattr(c, 'score', 0))
        print(f"  Top comment score: {getattr(top_comment, 'score', 0)}")
        print(f"  Top comment preview: {(getattr(top_comment, 'body', '') or '')[:120]}")
        print("\n✅ COMMENT FETCH WORKING")
    else:
        print("\n❌ NO COMMENTS FETCHED")


if __name__ == "__main__":
    main()
