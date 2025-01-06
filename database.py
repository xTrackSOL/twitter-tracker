import psycopg2
from psycopg2.extras import DictCursor
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.create_tables()

    def create_tables(self):
        with self.conn.cursor() as cur:
            with open('schema.sql', 'r') as f:
                cur.execute(f.read())
            self.conn.commit()

    def add_twitter_account(self, twitter_handle, channel_id):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tracked_accounts (twitter_handle, channel_id)
                VALUES (%s, %s)
                ON CONFLICT (twitter_handle, channel_id) DO NOTHING
                RETURNING id
            """, (twitter_handle, channel_id))
            self.conn.commit()
            return cur.fetchone()

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
            cur.execute("SELECT * FROM tracked_accounts")
            return cur.fetchall()

    def get_channel_accounts(self, channel_id):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT twitter_handle FROM tracked_accounts
                WHERE channel_id = %s
            """, (channel_id,))
            return [row['twitter_handle'] for row in cur.fetchall()]

    def close(self):
        self.conn.close()
