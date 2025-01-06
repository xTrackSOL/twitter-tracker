CREATE TABLE IF NOT EXISTS tracked_accounts (
    id SERIAL PRIMARY KEY,
    twitter_handle VARCHAR(15) NOT NULL,
    channel_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_tweet_id BIGINT DEFAULT NULL,
    UNIQUE(twitter_handle, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_tracked_accounts_channel 
ON tracked_accounts(channel_id);