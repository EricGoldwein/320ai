import sys
import os
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Add your project directory to the sys.path
    path = '/home/320/320ai'
    logger.info(f"Adding to sys.path: {path}")
    if path not in sys.path:
        sys.path.append(path)

    # Set the application root directory
    logger.info(f"Current working directory before chdir: {os.getcwd()}")
    os.chdir(path)
    logger.info(f"Current working directory after chdir: {os.getcwd()}")
    logger.info(f"Directory contents: {os.listdir(path)}")

    # Import your Flask app
    logger.info("Attempting to import Flask app...")
    from app import app as application
    logger.info("Successfully imported Flask app")

except Exception as e:
    logger.error(f"Error in WSGI configuration: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise 