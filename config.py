import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "myapp.log"
PROMPT_FILE = BASE_DIR / "prompt.txt"
YOUTUBE_IDS_FILE = BASE_DIR / "youtube_ids.json"
OUTPUT_DIR = BASE_DIR / "output_data"

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
YOUTUBE_API_KEY = os.getenv("GOOGLE_API")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


MEDIA_DB_ID = os.getenv("MEDIA_DB_ID")
ENTITIES_DB_ID = os.getenv("ENTITIES_DB_ID")
SNIPPETS_DB_ID = os.getenv("SNIPPETS_DB_ID")
