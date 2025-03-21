from PIL import Image

# Open the source image
img = Image.open('static/images/daisy_headshot.png')

# Create 16x16 favicon
favicon_16 = img.copy()
favicon_16.thumbnail((16, 16), Image.Resampling.LANCZOS)
favicon_16.save('static/images/favicon-16x16.png')

# Create 32x32 favicon
favicon_32 = img.copy()
favicon_32.thumbnail((32, 32), Image.Resampling.LANCZOS)
favicon_32.save('static/images/favicon-32x32.png')
favicon_32.save('static/images/favicon.ico')  # Save as ICO file

# Create 180x180 apple touch icon
apple_icon = img.copy()
apple_icon.thumbnail((180, 180), Image.Resampling.LANCZOS)
apple_icon.save('static/images/apple-touch-icon.png') 