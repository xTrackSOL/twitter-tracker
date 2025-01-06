from flask import Flask, render_template
import os

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', '')
# Updated permissions to include necessary bot permissions
DISCORD_PERMISSIONS = '537159744' # Permissions for bot management, message sending, and embed links
OAUTH_URL = f'https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&permissions={DISCORD_PERMISSIONS}&scope=bot%20applications.commands'

@app.route('/')
def index():
    return render_template('index.html', oauth_url=OAUTH_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)