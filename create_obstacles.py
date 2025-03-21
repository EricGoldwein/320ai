from PIL import Image, ImageDraw
import os

def create_dog():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Body
    draw.rectangle([20, 30, 44, 45], fill=(101, 67, 33))  # Brown body
    # Head
    draw.ellipse([10, 25, 25, 40], fill=(101, 67, 33))  # Brown head
    # Tail
    draw.polygon([(44, 35), (55, 30), (50, 40)], fill=(101, 67, 33))
    # Legs
    draw.rectangle([25, 45, 30, 55], fill=(101, 67, 33))  # Front leg
    draw.rectangle([35, 45, 40, 55], fill=(101, 67, 33))  # Back leg
    # Eye
    draw.ellipse([13, 29, 16, 32], fill=(0, 0, 0))
    
    return img

def create_bike():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Wheels
    draw.ellipse([10, 35, 25, 50], outline=(50, 50, 50), width=2)  # Front wheel
    draw.ellipse([40, 35, 55, 50], outline=(50, 50, 50), width=2)  # Back wheel
    # Frame
    draw.line([17, 42, 47, 42], fill=(30, 144, 255), width=3)  # Main frame
    draw.line([17, 42, 32, 25], fill=(30, 144, 255), width=3)  # Front frame
    draw.line([32, 25, 47, 42], fill=(30, 144, 255), width=3)  # Back frame
    # Handlebars
    draw.line([32, 25, 32, 20], fill=(30, 144, 255), width=2)
    draw.line([27, 20, 37, 20], fill=(30, 144, 255), width=2)
    
    return img

def create_child():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Head
    draw.ellipse([25, 10, 40, 25], fill=(255, 218, 185))
    # Body
    draw.rectangle([30, 25, 35, 45], fill=(255, 0, 0))  # Red shirt
    # Legs
    draw.rectangle([30, 45, 33, 55], fill=(0, 0, 255))  # Left leg
    draw.rectangle([34, 45, 37, 55], fill=(0, 0, 255))  # Right leg
    # Arms
    draw.line([25, 30, 30, 35], fill=(255, 218, 185), width=3)  # Left arm
    draw.line([35, 35, 40, 30], fill=(255, 218, 185), width=3)  # Right arm
    
    return img

def save_obstacles():
    # Create directory if it doesn't exist
    os.makedirs('static/images/game', exist_ok=True)
    
    # Create and save obstacles
    obstacles = {
        'dog': create_dog(),
        'bike': create_bike(),
        'child': create_child()
    }
    
    for name, img in obstacles.items():
        img.save(f'static/images/game/{name}.png')

if __name__ == '__main__':
    save_obstacles() 