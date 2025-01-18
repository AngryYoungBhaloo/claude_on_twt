# twitter_client.py
import os
import json
import requests
from requests_oauthlib import OAuth1Session
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dotenv import load_dotenv

class TwitterClientV2:
    def __init__(self):
        load_dotenv()

        # Load credentials
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET")

        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            raise ValueError("Missing Twitter API credentials in .env file")

        # Initialize OAuth1 session
        self.oauth = OAuth1Session(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret
        )

        # Get and store user ID on initialization
        self.user_id = self._get_my_user_id()
        if not self.user_id:
            raise ValueError("[TwitterClientV2] Could not get user ID. Check credentials.")

        # For storing new tweets posted by us
        self.my_handle = self._get_my_handle() or "MY_HANDLE"
        print(f"[TwitterClientV2] Initialized. user_id={self.user_id}, handle={self.my_handle}")

    def _get_my_user_id(self) -> Optional[str]:
        url = "https://api.twitter.com/2/users/me"
        resp = self.oauth.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data["data"]["id"]
        return None

    def _get_my_handle(self) -> Optional[str]:
        url = "https://api.twitter.com/2/users/me?user.fields=username"
        resp = self.oauth.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data["data"].get("username")
        return None

    def check_mentions(self, max_results=5) -> List[Dict]:
        """Get up to max_results mention tweets, store them as new unread tweets."""
        if not self.user_id:
            print("[TwitterClientV2] No user_id. Can't fetch mentions.")
            return []

        url = f"https://api.twitter.com/2/users/{self.user_id}/mentions"
        params = {
            "tweet.fields": "created_at,author_id,in_reply_to_user_id",
            "user.fields": "username",
            "max_results": max_results
        }
        resp = self.oauth.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            mentions = []
            for tweet in data.get("data", []):
                t_id = tweet["id"]
                tweet_data = {
                    "tweet_id": t_id,
                    "id": t_id,
                    "author_id": tweet.get("author_id"),
                    "text": tweet.get("text", ""),
                    "created_at": tweet.get("created_at"),
                    "is_read": False,
                    "parent_tweet_id": None  # We can't determine the actual parent tweet from just in_reply_to_user_id
                }
                mentions.append(tweet_data)
            return mentions
        else:
            print("[TwitterClientV2] check_mentions error:", resp.status_code, resp.text)
            return []

    def post_tweet(self, text: str) -> Optional[Dict]:
        """Post a new standalone tweet."""
        url = "https://api.twitter.com/2/tweets"
        payload = {"text": text}
        resp = self.oauth.post(url, json=payload)
        if resp.status_code == 201:
            data = resp.json()
            new_id = data["data"]["id"]
            return {
                "tweet_id": new_id,
                "id": new_id,
                "text": data["data"]["text"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": True,
                "parent_tweet_id": None,
                "by_author": self.my_handle
            }
        else:
            print("[TwitterClientV2] post_tweet error:", resp.status_code, resp.text)
            return None

    def reply_tweet(self, parent_id: str, text: str) -> Optional[Dict]:
        """Reply to an existing tweet."""
        url = "https://api.twitter.com/2/tweets"
        payload = {
            "text": text,
            "reply": {
                "in_reply_to_tweet_id": parent_id
            }
        }
        resp = self.oauth.post(url, json=payload)
        if resp.status_code == 201:
            data = resp.json()
            new_id = data["data"]["id"]
            return {
                "tweet_id": new_id,
                "id": new_id,
                "text": data["data"]["text"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": True,
                "parent_tweet_id": parent_id,
                "by_author": self.my_handle
            }
        else:
            print("[TwitterClientV2] reply_tweet error:", resp.status_code, resp.text)
            return None

    def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet via POST /2/users/:id/likes"""
        if not self.user_id:
            return False
        url = f"https://api.twitter.com/2/users/{self.user_id}/likes"
        payload = {"tweet_id": tweet_id}
        resp = self.oauth.post(url, json=payload)
        if resp.status_code == 201:
            print(f"[TwitterClientV2] Liked tweet {tweet_id}")
            return True
        else:
            print("[TwitterClientV2] like_tweet error:", resp.status_code, resp.text)
            return False

    def retweet_tweet(self, tweet_id: str) -> bool:
        """Retweet a tweet via POST /2/users/:id/retweets"""
        if not self.user_id:
            return False
        url = f"https://api.twitter.com/2/users/{self.user_id}/retweets"
        payload = {"tweet_id": tweet_id}
        resp = self.oauth.post(url, json=payload)
        if resp.status_code == 201:
            print(f"[TwitterClientV2] Retweeted tweet {tweet_id}")
            return True
        else:
            print("[TwitterClientV2] retweet_tweet error:", resp.status_code, resp.text)
            return False

    def quote_tweet(self, tweet_id: str, comment_text: str) -> Optional[Dict]:
        """
        "Quote tweet" by posting a new tweet that includes a link to the old tweet.
        We'll just use the partial link: https://twitter.com/i/web/status/<tweet_id>
        """
        quote_url = f"https://twitter.com/i/web/status/{tweet_id}"
        new_text = f"{comment_text}\n\n{quote_url}"
        return self.post_tweet(new_text)
