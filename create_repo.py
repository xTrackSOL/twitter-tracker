import os
import requests

def create_github_repository():
    token = os.getenv('GITHUB_TOKEN')
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    data = {
        'name': 'twitter-tracker',
        'description': 'A sophisticated multi-platform social media tracking and analytics bot with Telegram integration',
        'private': False,
        'has_issues': True,
        'has_wiki': True,
        'auto_init': False
    }
    
    response = requests.post(
        'https://api.github.com/user/repos',
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        print("Repository created successfully!")
        return True
    else:
        print(f"Failed to create repository: {response.json()}")
        return False

if __name__ == '__main__':
    create_github_repository()
