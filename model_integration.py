# model_integration.py
import os
import json
from typing import Dict, List
from anthropic import Anthropic

class ModelInterface:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Missing Anthropic API key in .env file")
        self.client = Anthropic(api_key=api_key)

    def decide_on_tweet_thread(self, thread: List[Dict]) -> Dict:
        """
        Show the entire thread to Claude, let it pick how to engage:
        - "like", "retweet", "quote", "reply", "post", or "do_nothing"
        Return JSON:
        {
          "action": "...",
          "tweet_id": "the tweet to engage with (if relevant)",
          "text": "text for post or reply or quote"
        }

        We'll assume the *first* tweet in 'thread' is the top-level tweet
        that triggered our viewing. 
        The rest are ancestors (above it) or descendants (replies).
        """
        if not thread:
            return {"action": "do_nothing"}

        # The top-level tweet is the first in the list if your get_full_thread 
        # is structured that way. (In our code, we do "ancestors + descendants",
        # which puts the top-level in the middle. So let's find it.)
        top_level_tweet = thread[len(thread)//2] if len(thread) > 0 else None

        # Format the thread for Claude
        formatted = []
        for idx, t in enumerate(thread):
            tid = t.get('tweet_id', 'unknown')
            author = t.get('author_id', 'unknown')
            text = t.get('text', '')
            is_top = ("<-- This is the main tweet we're focusing on" if t == top_level_tweet else "")
            msg = (
                f"Tweet #{idx+1}\n"
                f"Tweet ID: {tid}\n"
                f"Author: {author}\n"
                f"Text: {text}\n"
                f"{is_top}\n---\n"
            )
            formatted.append(msg)
        thread_str = "\n".join(formatted)

        prompt = f"""
You are chatting on Twitter, being friendly. Here is a full thread, 
including ancestors above the main tweet and replies below it:

{thread_str}

The *main tweet* we are focusing on is marked with "<-- This is the main tweet we're focusing on".

Please decide how to respond. Options:
- "like" a tweet
- "retweet" a tweet
- "quote" a tweet (create a new tweet referencing the old tweet's link)
- "reply" to a tweet
- "post" a brand-new tweet unrelated to the thread
- "do_nothing"

Output strictly JSON in this format:
{{
  "action": "...",
  "tweet_id": "the tweet you're liking/retweeting/replying/quoting if relevant",
  "text": "text if replying or quoting or posting a tweet"
}}

No extra commentary beyond that JSON.
"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",  # updated model name
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            content = response.content[0].text.strip()
            data = json.loads(content)
            return data
        except Exception as e:
            print(f"[ModelInterface] Error parsing model response: {e}")
            return {"action": "do_nothing"}
