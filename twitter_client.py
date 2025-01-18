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
            raise ValueError("Could not get user ID. Please check your credentials.")
        
        # Get user handle
        user_info = self._get_my_info()
        self.handle = user_info.get('username', 'unknown')
        print(f"[TwitterClientV2] Initialized. user_id={self.user_id}, handle={self.handle}")
            
    def _get_my_user_id(self) -> Optional[str]:
        """Get the authenticated user's ID"""
        url = "https://api.twitter.com/2/users/me"
        response = self.oauth.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data['data']['id']
        return None
    
    def _get_my_info(self) -> Dict:
        """Get the authenticated user's info"""
        url = "https://api.twitter.com/2/users/me"
        params = {
            "user.fields": "username,name,description"
        }
        response = self.oauth.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()['data']
        return {}

    def check_notifications(self, max_results: int = 5) -> List[Dict]:
        """Get mentions using v2 mentions endpoint"""
        if not self.user_id:
            print("[TwitterClientV2] No user ID available")
            return []

        url = f"https://api.twitter.com/2/users/{self.user_id}/mentions"
        params = {
            "tweet.fields": "created_at,author_id",
            "user.fields": "username",
            "max_results": max_results
        }
        
        response = self.oauth.get(url, params=params)
        print(f"[TwitterClientV2] Mentions check status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    'id': tweet['id'],
                    'tweet_id': tweet['id'],
                    'author_id': tweet['author_id'],
                    'text': tweet['text'],
                    'created_at': tweet.get('created_at')
                }
                for tweet in data.get('data', [])
            ]
        return []

    def post_tweet(self, text: str) -> Optional[Dict]:
        """Post a new tweet"""
        url = "https://api.twitter.com/2/tweets"
        payload = {"text": text}
        
        response = self.oauth.post(url, json=payload)
        print(f"[TwitterClientV2] Post tweet status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            return {
                'id': data['data']['id'],
                'tweet_id': data['data']['id'],
                'text': data['data']['text'],
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        return None

    def reply_tweet(self, parent_id: str, text: str) -> Optional[Dict]:
        """Reply to a tweet"""
        url = "https://api.twitter.com/2/tweets"
        payload = {
            "text": text,
            "reply": {
                "in_reply_to_tweet_id": parent_id
            }
        }
        
        response = self.oauth.post(url, json=payload)
        print(f"[TwitterClientV2] Reply tweet status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            return {
                'id': data['data']['id'],
                'tweet_id': data['data']['id'],
                'text': data['data']['text'],
                'in_reply_to_status_id': parent_id,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        return None

    def quote_tweet(self, tweet_id: str, text: str) -> Optional[Dict]:
        """Quote a tweet"""
        url = "https://api.twitter.com/2/tweets"
        payload = {
            "quote_tweet_id": tweet_id,
            "text": text
        }
        
        response = self.oauth.post(url, json=payload)
        print(f"[TwitterClientV2] Quote tweet status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            return {
                'id': data['data']['id'],
                'tweet_id': data['data']['id'],
                'text': data['data']['text'],
                'quoted_tweet_id': tweet_id,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        return None