import pathlib

from dotenv import load_dotenv

# Auto-load repo-root .env so job scripts don't need a manual `export $(cat .env | xargs)`.
load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")
