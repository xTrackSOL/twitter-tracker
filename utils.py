import discord
from config import COLORS

def create_tweet_embed(tweet, user):
    """Create a Discord embed for a tweet"""

    # Determine tweet type and color
    if hasattr(tweet, 'referenced_tweets') and tweet.get('referenced_tweets') and any(t.type == 'retweeted' for t in tweet['referenced_tweets']):
        color = COLORS['retweet']
    elif 'attachments' in tweet and tweet['attachments']:
        color = COLORS['media']
    else:
        color = COLORS['text']

    embed = discord.Embed(
        description=tweet['text'],
        color=color,
        timestamp=tweet['created_at']
    )

    # Set author information
    embed.set_author(
        name=f"{user['name']} (@{user['username']})",
        url=f"https://twitter.com/{user['username']}/status/{tweet['id']}",
        icon_url=user['profile_image_url'] if user['profile_image_url'] else None
    )

    # Add metrics
    embed.add_field(
        name="Stats",
        value=f"💬 {tweet['public_metrics']['reply_count']} "
              f"🔄 {tweet['public_metrics']['retweet_count']} "
              f"❤️ {tweet['public_metrics']['like_count']}"
    )

    # Add media if present
    if 'attachments' in tweet and 'media' in tweet['attachments']:
        first_media = tweet['attachments']['media'][0]
        if first_media['type'] == 'photo':
            embed.set_image(url=first_media['url'])

    return embed

def format_error_message(error):
    """Format error messages for Discord display"""
    return discord.Embed(
        title="Error",
        description=str(error),
        color=discord.Color.red()
    )