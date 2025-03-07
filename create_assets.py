from PIL import Image, ImageDraw
import os

def create_track_background(width=800, height=600):
    """Create a simple track background."""
    img = Image.new('RGB', (width, height), '#87CEEB')  # Sky blue
    draw = ImageDraw.Draw(img)
    
    # Green field
    draw.rectangle([0, height//2, width, height], fill='#90EE90')
    
    # Brown track
    draw.ellipse([50, 200, width-50, height-50], fill='#8B4513')
    draw.ellipse([100, 250, width-100, height-100], fill='#90EE90')
    
    # White lines
    for i in range(6):
        draw.ellipse([75+i*10, 225+i*10, width-75-i*10, height-75-i*10], outline='white')
    
    return img

def create_horse_sprite(size=128, color='#8B4513'):
    """Create a simple horse sprite."""
    img = Image.new('RGBA', (size * 8, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    for frame in range(8):
        x_offset = frame * size
        
        # Body
        draw.rectangle([x_offset + 30, 40, x_offset + 90, 80], fill=color)
        
        # Head
        draw.rectangle([x_offset + 10, 30, x_offset + 30, 50], fill=color)
        
        # Legs (animated)
        leg_offset = 10 if frame % 2 == 0 else 0
        draw.rectangle([x_offset + 40, 80 + leg_offset, x_offset + 50, 110], fill=color)
        draw.rectangle([x_offset + 70, 80 - leg_offset, x_offset + 80, 110], fill=color)
        
        # Eye
        draw.ellipse([x_offset + 15, 35, x_offset + 20, 40], fill='black')
    
    return img

def create_obstacle(size=64):
    """Create a simple hurdle."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Vertical poles
    draw.rectangle([10, 10, 20, size-10], fill='brown')
    draw.rectangle([size-20, 10, size-10, size-10], fill='brown')
    
    # Horizontal bar
    draw.rectangle([10, 20, size-10, 30], fill='white')
    
    return img

def main():
    # Create directory
    os.makedirs('static/images/game', exist_ok=True)
    
    # Create and save track
    track = create_track_background()
    track.save('static/images/game/track.png')
    
    # Create and save Daisy
    daisy = create_horse_sprite(color='#8B4513')  # Brown
    daisy.save('static/images/game/daisy.png')
    
    # Create and save other runners
    colors = ['#8B0000', '#006400', '#4B0082']  # Dark red, dark green, indigo
    for i, color in enumerate(colors):
        runner = create_horse_sprite(color=color)
        runner.save(f'static/images/game/runner_{i+1}.png')
    
    # Create and save obstacle
    obstacle = create_obstacle()
    obstacle.save('static/images/game/obstacle.png')
    
    print("Asset creation complete!")

if __name__ == '__main__':
    main() 