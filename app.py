import os
import logging
from flask import Flask, request, jsonify, render_template, url_for, send_from_directory, session, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import random
from datetime import datetime
import sqlite3
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
import time
import httpx
import openai

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize environment variables first
logger.info("Loading environment variables...")
load_dotenv()

# Get environment variables with defaults
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
logger.info(f"API Key present: {bool(OPENAI_API_KEY)}")
if not OPENAI_API_KEY:
    logger.error("No OpenAI API key found in environment variables!")

ASSISTANT_ID = os.environ.get('ASSISTANT_ID', 'asst_ThPrNwQfjvTWDUkDlp5XwvCm')
logger.info(f"Using Assistant ID: {ASSISTANT_ID}")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

@app.route('/test-openai')
def test_openai():
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'OpenAI is working!'"}]
        )
        return jsonify({
            "success": True,
            "message": response.choices[0].message.content,
            "api_key_exists": bool(os.getenv('OPENAI_API_KEY')),
            "openai_version": openai.__version__
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "api_key_exists": bool(os.getenv('OPENAI_API_KEY')),
            "openai_version": openai.__version__
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 