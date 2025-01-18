#ingest_tweet.py
import argparse
import os
from rag import TweetStore

def main():
    parser = argparse.ArgumentParser(description="Manually ingest a tweet into local storage.")
    parser.add_argument("--tweet_id", required=True, help="The ID of the tweet.")
    parser.add_argument("--author_id", required=True, help="The ID of the tweet author.")
    parser.add_argument("--text", required=True, help="The text of the tweet.")
    parser.add_argument("--parent_tweet_id", default=None, help="The parent tweet ID if this is a reply.")
    parser.add_argument("--url", default="", help="Optional URL of the tweet.")

    args = parser.parse_args()

    # Initialize the TweetStore
    store = TweetStore()

    # Build the tweet data
    new_tweet = {
        "tweet_id": args.tweet_id,
        "id": args.tweet_id,  # for backward-compat
        "author_id": args.author_id,
        "text": args.text,
        "created_at": None,
        "is_read": False,
        "parent_tweet_id": args.parent_tweet_id,
        "url": args.url
    }

    try:
        store.store_tweet(new_tweet)
        print(f"Successfully stored tweet {args.tweet_id}")
    except Exception as e:
        print(f"Failed to store tweet: {str(e)}")

if __name__ == "__main__":
    main()
