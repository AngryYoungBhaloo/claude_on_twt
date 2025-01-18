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
        """Handle tweet thread decisions"""
        if not thread:
            return self.get_proactive_action()

        # Rest of the thread handling code remains the same
        top_level_tweet = thread[len(thread)//2] if len(thread) > 0 else None

        formatted = []
        for idx, t in enumerate(thread):
            tid = t.get('tweet_id', t.get('id', 'unknown'))
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
You are chatting on Twitter about AI, tech, and interesting ideas. Here is a thread to engage with:

{thread_str}

The *main tweet* we are focusing on is marked above.

How would you like to engage? Output JSON only:
{{
  "action": "like"|"retweet"|"quote"|"reply"|"post"|"do_nothing",
  "tweet_id": "ID if liking/retweeting/replying/quoting",
  "text": "your text if posting/replying/quoting"
}}
"""

        return self._get_model_response(prompt)

    def get_proactive_action(self) -> Dict:
        """Decide what to post when there's no thread to engage with"""
        prompt = """
You're managing an AI/Tech Twitter account. There are no new interactions to respond to.

What would you like to post? Consider:
- Sharing thoughts about AI developments
- Starting interesting discussions
- Asking engaging questions
- Making observations about tech trends

Output only JSON:
{
  "action": "post",
  "tweet_id": null,
  "text": "your tweet text"
}
"""
        return self._get_model_response(prompt)

    def _get_model_response(self, prompt: str) -> Dict:
        """Helper to handle model calls and response parsing"""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            print(f"[ModelInterface] Raw response: {content}")  # Debug output
            data = json.loads(content)
            return data
        except Exception as e:
            print(f"[ModelInterface] Error getting model response: {e}")
            return {"action": "do_nothing"}

