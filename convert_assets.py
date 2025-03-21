import os
import cairosvg

def convert_svg_to_png(input_path, output_path):
    """Convert SVG file to PNG format."""
    cairosvg.svg2png(url=input_path, write_to=output_path)

def main():
    # Create game assets directory if it doesn't exist
    os.makedirs('static/images/game', exist_ok=True)
    
    # Convert track background
    convert_svg_to_png(
        'static/images/game/track.svg',
        'static/images/game/track.png'
    )
    
    # Convert Daisy sprite sheet
    convert_svg_to_png(
        'static/images/game/daisy.svg',
        'static/images/game/daisy.png'
    )
    
    # Convert obstacle sprite
    convert_svg_to_png(
        'static/images/game/obstacle.svg',
        'static/images/game/obstacle.png'
    )
    
    print("Asset conversion complete!")

if __name__ == '__main__':
    main() 