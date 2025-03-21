from PIL import Image
import os

def create_sprite(input_path, output_path, size=(64, 64), force_size=None):
    print(f"Processing {input_path} to {output_path}")
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found!")
        return False
    
    try:
        # Open the image
        img = Image.open(input_path)
        print(f"Original image size: {img.size}, mode: {img.mode}")
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            print("Converted to RGBA mode")
        
        # Create a new transparent image
        new_img = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # If force_size is provided, use it instead of calculating
        if force_size:
            new_size = force_size
            print(f"Using forced size: {new_size}")
        # If image is smaller than target size, don't scale up
        elif img.width <= size[0] and img.height <= size[1]:
            new_size = (img.width, img.height)
            print("Image is smaller than target size, keeping original size")
        else:
            # Calculate scaling factor to fit within the square while maintaining aspect ratio
            scale = min(size[0] / img.width, size[1] / img.height)
            new_size = (int(img.width * scale), int(img.height * scale))
            print(f"Scaling to: {new_size}")
        
        # Resize the original image
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Calculate position to center the image
        x = (size[0] - new_size[0]) // 2
        y = (size[1] - new_size[1]) // 2
        print(f"Centering at position: ({x}, {y})")
        
        # Paste the resized image onto the transparent background
        new_img.paste(img, (x, y), img)
        
        # Save the result
        new_img.save(output_path, 'PNG')
        print(f"Saved sprite to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        return False

def main():
    # Create sprites directory if it doesn't exist
    if not os.path.exists('static/images/game2/sprites'):
        os.makedirs('static/images/game2/sprites')
        print("Created sprites directory")
    
    success = True
    
    # Process Bear Trident.png with larger size
    if not create_sprite(
        'static/images/game2/Bear Trident.png',
        'static/images/game2/sprites/bear_trident_sprite.png',
        size=(64, 64),
        force_size=(50, 50)  # Force larger size for bear trident
    ):
        success = False
    
    # Process sneaks.jpg
    if not create_sprite(
        'static/images/game2/sneaks.jpg',
        'static/images/game2/sprites/sneaks_sprite.png'
    ):
        success = False
    
    if success:
        print("All sprites created successfully!")
    else:
        print("Some sprites failed to create. Check the errors above.")

if __name__ == "__main__":
    main() 