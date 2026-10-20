import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Load GEMINI API key from environment. Do NOT hardcode secrets here.
# If the key is not present, `GEMINI_API_KEY` will be None and the app
# will use a local fallback for question generation.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")