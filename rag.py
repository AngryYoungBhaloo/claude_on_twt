# rag.py
import json
import faiss
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional

class TweetStore:
    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = storage_dir
        self.tweets_file = os.path.join(storage_dir, "tweets.json")

        # Create storage directory if needed
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

        # Load or init tweets
        if os.path.exists(self.tweets_file):
            with open(self.tweets_file, "r") as f:
                self.tweets = json.load(f)
        else:
            self.tweets = []

        # Initialize embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embedding_size = 384

        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(self.embedding_size)
        if self.tweets:
            embeddings = [self.model.encode(t["text"]) for t in self.tweets]
            self.index.add(np.array(embeddings))

        print(f"[TweetStore] Loaded {len(self.tweets)} tweets from storage")

    def _save_tweets(self):
        """Save tweets to JSON file"""
        with open(self.tweets_file, "w") as f:
            json.dump(self.tweets, f, indent=2)
        print(f"[TweetStore] Saved {len(self.tweets)} tweets to storage")

    def store_tweet(self, tweet_data: Dict):
        """Store a tweet, handling both id and tweet_id fields"""
        # Ensure we have required fields
        tweet_id = tweet_data.get('tweet_id') or tweet_data.get('id')
        if not tweet_id or 'text' not in tweet_data:
            raise ValueError("Tweet data must have ID and text fields")

        # Standardize the data structure
        normalized_tweet = {
            'tweet_id': tweet_id,
            'id': tweet_id,  # Keep both for compatibility
            'text': tweet_data['text'],
            'author_id': tweet_data.get('author_id'),
            'created_at': tweet_data.get('created_at'),
            'in_reply_to_status_id': tweet_data.get('in_reply_to_status_id'),
            'quoted_tweet_id': tweet_data.get('quoted_tweet_id'),
            'is_read': tweet_data.get('is_read', False)
        }

        # Update existing or add new
        existing_idx = None
        for i, t in enumerate(self.tweets):
            if t.get('tweet_id') == tweet_id or t.get('id') == tweet_id:
                existing_idx = i
                break

        if existing_idx is not None:
            self.tweets[existing_idx].update(normalized_tweet)
        else:
            self.tweets.append(normalized_tweet)
            # Add new embedding
            embedding = self.model.encode(normalized_tweet['text'])
            self.index.add(np.array([embedding]))

        self._save_tweets()

    def get_next_unread_tweet(self) -> Optional[Dict]:
        """Get oldest unread tweet"""
        for tweet in self.tweets:
            if not tweet.get('is_read', False):
                return tweet
        return None

    def mark_tweet_as_read(self, tweet_id: str):
        """Mark tweet as read"""
        for tweet in self.tweets:
            if tweet.get('tweet_id') == tweet_id or tweet.get('id') == tweet_id:
                tweet['is_read'] = True
                break
        self._save_tweets()

    def get_thread(self, tweet_id: str) -> List[Dict]:
        """Get a tweet's thread (original tweet + context)"""
        # Find the tweet
        tweet = next((t for t in self.tweets if t.get('tweet_id') == tweet_id or t.get('id') == tweet_id), None)
        if not tweet:
            print(f"[TweetStore] Tweet {tweet_id} not found")
            return []

        thread = [tweet]  # Start with the tweet itself

        # Add reply-to tweet if it exists
        if tweet.get('in_reply_to_status_id'):
            parent = next((t for t in self.tweets if 
                t.get('tweet_id') == tweet['in_reply_to_status_id'] or 
                t.get('id') == tweet['in_reply_to_status_id']), None)
            if parent:
                thread.insert(0, parent)

        # Add quoted tweet if it exists
        if tweet.get('quoted_tweet_id'):
            quoted = next((t for t in self.tweets if 
                t.get('tweet_id') == tweet['quoted_tweet_id'] or 
                t.get('id') == tweet['quoted_tweet_id']), None)
            if quoted:
                thread.append(quoted)

        return thread

    def retrieve_context(self, query: str, k: int = 5) -> List[Dict]:
        """Find similar tweets"""
        if not self.tweets:
            return []
        query_emb = self.model.encode(query)
        D, I = self.index.search(np.array([query_emb]), min(k, len(self.tweets)))
        return [self.tweets[i] for i in I[0] if i < len(self.tweets)]