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

    def _save_tweets(self):
        with open(self.tweets_file, "w") as f:
            json.dump(self.tweets, f, indent=2)

    def store_tweet(self, tweet_data: Dict):
        """
        Store or update a tweet in local JSON.
        Must contain: 'tweet_id', 'text' minimally.
        If 'is_read' isn't provided, default to False.
        """
        if "tweet_id" not in tweet_data or "text" not in tweet_data:
            raise ValueError("Tweet data must have 'tweet_id' and 'text'.")

        if "is_read" not in tweet_data:
            tweet_data["is_read"] = False

        existing_idx = None
        for i, t in enumerate(self.tweets):
            if t["tweet_id"] == tweet_data["tweet_id"]:
                existing_idx = i
                break

        if existing_idx is not None:
            # Update existing tweet data
            self.tweets[existing_idx] = tweet_data
        else:
            # Add new
            self.tweets.append(tweet_data)

            # Add new embedding to the FAISS index
            embedding = self.model.encode(tweet_data["text"])
            self.index.add(np.array([embedding]))

        self._save_tweets()

    def get_next_unread_tweet(self) -> Optional[Dict]:
        """
        Return the oldest unread tweet (FIFO) from self.tweets.
        We'll assume the order in self.tweets is insertion order for simplicity.
        """
        for t in self.tweets:
            if not t.get("is_read", False):
                return t
        return None

    def mark_tweet_as_read(self, tweet_id: str):
        """Mark the specific tweet as read."""
        for t in self.tweets:
            if t["tweet_id"] == tweet_id:
                t["is_read"] = True
                break
        self._save_tweets()

    def retrieve_context(self, query: str, k: int = 5) -> List[Dict]:
        """Return up to k most similar tweets to the query from FAISS."""
        if not self.tweets:
            return []
        query_emb = self.model.encode(query)
        D, I = self.index.search(np.array([query_emb]), min(k, len(self.tweets)))
        return [self.tweets[i] for i in I[0] if i < len(self.tweets)]

    def get_tweet(self, tweet_id: str) -> Optional[Dict]:
        """Return a tweet object by ID."""
        for t in self.tweets:
            if t["tweet_id"] == tweet_id:
                return t
        return None

    def get_full_thread(self, tweet_id: str) -> List[Dict]:
        """
        Return the entire thread of the tweet (ancestors + tweet + descendants).
        We'll do:
        - Upward: climb .parent_tweet_id
        - Downward: gather children recursively
        Then combine them in a single list, with ancestors first, 
        the main tweet in the middle, and then descendants.
        """
        # 1) Ancestors
        ancestors = []
        curr_id = tweet_id
        while True:
            tw = self.get_tweet(curr_id)
            if not tw:
                break
            ancestors.append(tw)
            parent_id = tw.get("parent_tweet_id")
            if not parent_id:
                break
            curr_id = parent_id
        ancestors.reverse()  # oldest ancestor first, main tweet last

        # 2) Descendants
        descendants = self._gather_descendants(tweet_id)

        # The main tweet will appear in both ancestors (as last element) 
        # and descendants (as first element). We'll unify them carefully.
        # For clarity, let's unify them so the main tweet doesn't duplicate.
        if descendants:
            # The first item in descendants is the main tweet
            return ancestors[:-1] + descendants
        else:
            # If no descendants, ancestors alone suffices
            return ancestors

    def _gather_descendants(self, root_id: str) -> List[Dict]:
        """Recursively gather all tweet descendants of root_id (including root_id as the first)."""
        root_tweet = self.get_tweet(root_id)
        if not root_tweet:
            return []
        results = [root_tweet]
        children = [t for t in self.tweets if t.get("parent_tweet_id") == root_id]
        for child in children:
            results.extend(self._gather_descendants(child["tweet_id"]))
        return results
