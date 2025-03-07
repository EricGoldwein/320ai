import os
import requests
from pathlib import Path

def download_file(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {filename}")

def main():
    # Create game2 directory if it doesn't exist
    game2_dir = Path('static/images/game2')
    game2_dir.mkdir(parents=True, exist_ok=True)

    # Asset URLs (these are placeholder URLs - I'll replace them with actual asset URLs)
    assets = {
        'daisy.png': 'https://raw.githubusercontent.com/your-repo/pixel-horse/main/horse.png',
        'porcupine.png': 'https://raw.githubusercontent.com/your-repo/pixel-porcupine/main/porcupine.png',
        'snake.png': 'https://raw.githubusercontent.com/your-repo/pixel-snake/main/snake.png',
        'horse.png': 'https://raw.githubusercontent.com/your-repo/pixel-horse-2/main/horse.png',
        'yellowstone.png': 'https://raw.githubusercontent.com/your-repo/pixel-mountains/main/mountains.png',
        'river.png': 'https://raw.githubusercontent.com/your-repo/pixel-river/main/river.png',
        'grass.png': 'https://raw.githubusercontent.com/your-repo/pixel-grass/main/grass.png'
    }

    # Download each asset
    for filename, url in assets.items():
        filepath = game2_dir / filename
        download_file(url, filepath)

if __name__ == '__main__':
    main() 