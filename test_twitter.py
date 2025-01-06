import asyncio
from twitter_client import TwitterClient

async def test_twitter_tracking():
    client = TwitterClient()

    # Test user lookup
    test_username = "NASA"  # Using NASA's account as it's very active
    print(f"\nTesting user lookup for @{test_username}")
    print("Trying different Nitter instances...")

    user = await client.get_user_by_username(test_username)
    print(f"User found: {user is not None}")
    if user:
        print(f"User name: {user['name']}")
        print(f"Username: @{user['username']}")
        print(f"Profile image: {user['profile_image_url']}")

        # Test tweet fetching
        print(f"\nFetching recent tweets from @{test_username}")
        tweets = await client.get_recent_tweets(user['id'])
        print(f"Number of tweets found: {len(tweets)}")

        if tweets:
            print("\nMost recent tweet:")
            print(f"Text: {tweets[0]['text']}")
            print(f"Created at: {tweets[0]['created_at']}")
            if 'attachments' in tweets[0]:
                print(f"Media attachments: {len(tweets[0]['attachments'].get('media', []))}")
        else:
            print("No tweets found")
    else:
        print("Failed to find user")

if __name__ == "__main__":
    asyncio.run(test_twitter_tracking())