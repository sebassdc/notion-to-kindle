import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_EMAIL = os.environ.get("GMAIL_EMAIL")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")

KINDLE_EMAIL = os.environ.get("KINDLE_EMAIL")

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
