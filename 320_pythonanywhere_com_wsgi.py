import sys
import os

# Add your project directory to the sys.path
path = '/home/320/320ai'
if path not in sys.path:
    sys.path.append(path)

# Import your Flask app
from app import app as application 