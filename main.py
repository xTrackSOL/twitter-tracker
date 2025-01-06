from flask import Flask, render_template
import os

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', '')
DISCORD_PERMISSIONS = '67584' # Permissions for sending messages and managing messages
OAUTH_URL = f'https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&permissions={DISCORD_PERMISSIONS}&scope=bot%20applications.commands'

@app.route('/')
def index():
    return render_template('index.html', oauth_url=OAUTH_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)