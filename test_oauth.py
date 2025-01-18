# test_oauth.py
from twitter_client import TwitterClientV2

def main():
    print("Testing Twitter API authentication with OAuth 1.0a...")
    try:
        client = TwitterClientV2()
        
        print("\nTesting post tweet...")
        result = client.post_tweet("Test tweet from my AI bot!")
        if result:
            print(f"Successfully posted tweet with ID: {result['tweet_id']}")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")

if __name__ == "__main__":
    main()