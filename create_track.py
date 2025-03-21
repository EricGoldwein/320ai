from PIL import Image, ImageDraw

def create_track():
    # Create a large image for seamless tiling
    width = 800
    height = 600
    
    img = Image.new('RGBA', (width, height), (135, 206, 235))  # Sky blue background
    draw = ImageDraw.Draw(img)
    
    # Draw grass
    draw.rectangle([0, height//2, width, height], fill=(34, 139, 34))  # Forest green
    
    # Draw track lanes
    lane_colors = [(210, 180, 140), (200, 170, 130), (190, 160, 120)]  # Different shades of tan
    lane_heights = [150, 300, 450]
    lane_width = 100
    
    for i, y in enumerate(lane_heights):
        draw.rectangle([0, y - lane_width//2, width, y + lane_width//2], 
                      fill=lane_colors[i])
        
        # Add lane markers
        marker_width = 20
        for x in range(0, width, 100):
            draw.rectangle([x, y-2, x+marker_width, y+2], 
                         fill=(255, 255, 255))
    
    # Save the image
    img.save('static/images/game/track.png')

if __name__ == '__main__':
    create_track() 