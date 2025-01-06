from flask import Flask, render_template
import os
from urllib.parse import quote

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', '')
DISCORD_PERMISSIONS = '537159744'  # Bot management, message sending, embed links
OAUTH_URL = (
    'https://discord.com/api/oauth2/authorize'
    f'?client_id={DISCORD_CLIENT_ID}'
    f'&permissions={DISCORD_PERMISSIONS}'
    '&scope=bot%20applications.commands'
)

TELEGRAM_BOT_USERNAME = 'xTrackSOL_bot'

@app.route('/')
def index():
    return render_template('index.html', oauth_url=OAUTH_URL, bot_username=TELEGRAM_BOT_USERNAME)

if __name__ == '__main__':
    # Ensure we're binding to all network interfaces
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)