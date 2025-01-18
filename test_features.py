# test_features.py
from twitter_client import TwitterClientV2
import time

def test_all_features():
    print("\n=== Testing All Bot Features ===\n")
    
    try:
        # Initialize client
        print("1. Initializing Twitter client...")
        client = TwitterClientV2()
        
        # Test post tweet
        print("\n2. Testing post tweet...")
        tweet = client.post_tweet("Testing my AI bot's features! 🤖 #TwitterAPI")
        if tweet:
            print(f"✅ Successfully posted tweet: {tweet['tweet_id']}")
            original_tweet_id = tweet['tweet_id']
            
            # Test reply to our own tweet
            print("\n3. Testing reply to tweet...")
            time.sleep(2)  # Small delay to avoid rate limits
            reply = client.reply_tweet(original_tweet_id, "This is a reply to test the reply feature! 📝")
            if reply:
                print(f"✅ Successfully posted reply: {reply['tweet_id']}")
            
        # Test checking notifications
        print("\n4. Testing notifications check...")
        notifications = client.check_notifications()
        print(f"Found {len(notifications)} notifications")
        for notif in notifications:
            print(f"- Notification from user {notif['author_id']}: {notif['text'][:50]}...")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    test_all_features()