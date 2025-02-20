import psycopg2
from psycopg2.extras import DictCursor
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        self.create_tables()

    def create_tables(self):
        with self.conn.cursor() as cur:
            with open('schema.sql', 'r') as f:
                cur.execute(f.read())
            self.conn.commit()

    def add_twitter_account(self, twitter_handle, channel_id, last_tweet_id=None):
        """Add a Twitter account to track with optional last_tweet_id"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tracked_accounts (twitter_handle, channel_id, last_tweet_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (twitter_handle, channel_id) DO UPDATE 
                SET last_tweet_id = EXCLUDED.last_tweet_id
                RETURNING id
            """, (twitter_handle, channel_id, last_tweet_id))
            self.conn.commit()
            result = cur.fetchone()
            return result[0] if result else None

    def remove_twitter_account(self, twitter_handle, channel_id):
        with self.conn.cursor() as cur:
            cur.execute("""
                DELETE FROM tracked_accounts
                WHERE twitter_handle = %s AND channel_id = %s
                RETURNING id
            """, (twitter_handle, channel_id))
            self.conn.commit()
            return cur.fetchone() is not None

    def get_tracked_accounts(self):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT id, twitter_handle, channel_id, last_tweet_id, created_at
                FROM tracked_accounts
            """)  # Explicitly select all columns
            return [dict(row) for row in cur.fetchall()]  # Convert to dictionary

    def get_channel_accounts(self, channel_id):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT twitter_handle FROM tracked_accounts
                WHERE channel_id = %s
            """, (channel_id,))
            return [row['twitter_handle'] for row in cur.fetchall()]

    def update_last_tweet_id(self, twitter_handle, channel_id, tweet_id):
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE tracked_accounts
                SET last_tweet_id = %s
                WHERE twitter_handle = %s AND channel_id = %s
            """, (tweet_id, twitter_handle, channel_id))
            self.conn.commit()

    def close(self):
        self.conn.close()