# main.py
import schedule
import time
from datetime import datetime, timezone

from twitter_client import TwitterClientV2
from rag import TweetStore
from model_integration import ModelInterface

class TwitterBot:
    def __init__(self, max_actions_per_cycle=3):
        """
        max_actions_per_cycle: how many total "actions" the bot can do 
        in a single 15-min run_cycle. Each tweet engagement is 1 action.
        """
        self.twitter = TwitterClientV2()
        self.store = TweetStore()
        self.model = ModelInterface()

        self.max_actions_per_cycle = max_actions_per_cycle
        self.actions_taken = 0  # reset each cycle

    def run_cycle(self):
        """
        The main bot cycle, scheduled every 15 minutes. 
        1) Fetch new mention tweets (up to N=3).
        2) Engage with unread tweets from the local store, 
           up to self.max_actions_per_cycle times.
        """
        try:
            print(f"\n[Bot] Starting cycle at {datetime.now(timezone.utc).isoformat()}")
            self.actions_taken = 0

            # 1) Always fetch the latest 5 mentions
            new_mentions = self.twitter.check_mentions(max_results=5)
            if new_mentions:
                print(f"[Bot] Fetched {len(new_mentions)} new mention(s). Storing them.")
                for mention in new_mentions:
                    self.store.store_tweet(mention)
            else:
                print("[Bot] No new mentions found.")

            # 2) Now engage with up to max_actions_per_cycle unread tweets
            while self.actions_taken < self.max_actions_per_cycle:
                tweet = self.store.get_next_unread_tweet()
                if not tweet:
                    print("[Bot] No unread tweets in the queue.")
                    break

                # Build the full thread (ancestors + this tweet + descendants)
                full_thread = self.store.get_full_thread(tweet["tweet_id"])

                # Ask Claude how to engage with this thread
                decision = self.model.decide_on_tweet_thread(full_thread)
                self.actions_taken += 1

                # Parse the decision
                action = decision.get("action", "do_nothing")
                action_tweet_id = decision.get("tweet_id")
                text = decision.get("text", "")

                if action == "like" and action_tweet_id:
                    print(f"[Bot] Liking tweet: {action_tweet_id}")
                    self.twitter.like_tweet(action_tweet_id)

                elif action == "retweet" and action_tweet_id:
                    print(f"[Bot] Retweeting tweet: {action_tweet_id}")
                    self.twitter.retweet_tweet(action_tweet_id)

                elif action == "quote" and action_tweet_id:
                    print(f"[Bot] Quoting tweet: {action_tweet_id}")
                    result = self.twitter.quote_tweet(action_tweet_id, text)
                    if result:
                        self.store.store_tweet(result)

                elif action == "reply" and action_tweet_id:
                    print(f"[Bot] Replying to tweet: {action_tweet_id}")
                    result = self.twitter.reply_tweet(action_tweet_id, text)
                    if result:
                        self.store.store_tweet(result)

                elif action == "post":
                    print("[Bot] Posting a new tweet...")
                    result = self.twitter.post_tweet(text)
                    if result:
                        self.store.store_tweet(result)

                else:
                    print("[Bot] Doing nothing with this thread.")

                # Mark the top-level tweet as read (not the whole thread)
                self.store.mark_tweet_as_read(tweet["tweet_id"])

        except Exception as e:
            print(f"[Bot] Error in bot cycle: {str(e)}")

    def start(self):
        """
        Start the scheduled job: one run_cycle immediately, 
        then every 15 minutes.
        """
        print("[Bot] Starting up. Running initial cycle now...")
        self.run_cycle()

        schedule.every(15).minutes.do(self.run_cycle)

        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    # You can pass in a different max_actions_per_cycle if you like
    bot = TwitterBot(max_actions_per_cycle=3)
    bot.start()

if __name__ == "__main__":
    main()
