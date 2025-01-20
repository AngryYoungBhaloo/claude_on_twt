# test_auth.py
from twitter_client import TwitterClientV2

def main():
    print("Testing Twitter API authentication...")
    try:
        client = TwitterClientV2()
        print("Authentication test complete!")
    except Exception as e:
        print(f"Error during authentication: {str(e)}")

if __name__ == "__main__":
    main()