from datetime import datetime, timezone
import time  # Added back for sleep() function

from twitter_client import TwitterClientV2
from rag import TweetStore
from model_integration import ModelInterface

class TwitterBot:
    def __init__(self, max_actions_per_cycle=3):
        self.twitter = TwitterClientV2()
        self.store = TweetStore()
        self.model = ModelInterface()
        self.max_actions_per_cycle = max_actions_per_cycle
        self.actions_taken = 0

    def run_cycle(self):
        """Main bot cycle with proactive posting"""
        try:
            print(f"\n[Bot] Starting cycle at {datetime.now(timezone.utc).isoformat()}")
            self.actions_taken = 0

            # 1) Check for new mentions
            new_mentions = self.twitter.check_notifications()
            if new_mentions:
                print(f"[Bot] Found {len(new_mentions)} new mention(s)")
                for mention in new_mentions:
                    self.store.store_tweet(mention)

            # 2) Process stored tweets or be proactive
            while self.actions_taken < self.max_actions_per_cycle:
                # First try to get an unread tweet
                tweet = self.store.get_next_unread_tweet() if hasattr(self.store, 'get_next_unread_tweet') else None
                
                if tweet:
                    # Process existing tweet
                    thread = self.store.get_thread(tweet['tweet_id'])
                    decision = self.model.decide_on_tweet_thread(thread)
                else:
                    # No tweets to process, get proactive action
                    print("[Bot] No unread tweets. Getting proactive action...")
                    decision = self.model.get_proactive_action()

                print(f"[Bot] Model decision: {decision}")
                
                # Execute the decision
                action = decision.get("action", "do_nothing")
                tweet_id = decision.get("tweet_id")
                text = decision.get("text", "")

                if action == "post":
                    print("[Bot] Posting new tweet...")
                    result = self.twitter.post_tweet(text)
                    if result:
                        self.store.store_tweet(result)
                        print(f"[Bot] Successfully posted: {text}")
                elif action == "reply" and tweet_id:
                    result = self.twitter.reply_tweet(tweet_id, text)
                    if result:
                        self.store.store_tweet(result)
                        print(f"[Bot] Successfully replied to {tweet_id}")
                    else:
                        print(f"[Bot] Failed to reply to tweet {tweet_id}")
                elif action == "quote" and tweet_id:
                    result = self.twitter.quote_tweet(tweet_id, text)
                    if result:
                        self.store.store_tweet(result)
                        print(f"[Bot] Successfully quoted tweet {tweet_id}")
                    else:
                        print(f"[Bot] Failed to quote tweet {tweet_id}")

                self.actions_taken += 1

                # If we were processing a stored tweet, mark it as read
                if tweet and hasattr(self.store, 'mark_tweet_as_read'):
                    self.store.mark_tweet_as_read(tweet['tweet_id'])

                # Small delay between actions
                time.sleep(2)

        except Exception as e:
            print(f"[Bot] Error in bot cycle: {str(e)}")
            raise  # Re-raise the exception for GitHub Actions to catch failures

def main():
    bot = TwitterBot(max_actions_per_cycle=3)
    bot.run_cycle()  # Just run once and exit

if __name__ == "__main__":
    main()