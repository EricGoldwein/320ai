import os

# OpenAI API Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')  # Get from environment variable

# Assistant Configuration
ASSISTANT_ID = "asst_ThPrNwQfjvTWDUkDlp5XwvCm"  # Your DAISY assistant ID

# API Configuration
MAX_RETRIES = 3
TIMEOUT = 30  # seconds

# Rate Limiting
RATE_LIMIT = "30 per minute" 