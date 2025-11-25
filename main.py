import json
import logging
import os
import sys

from dotenv import load_dotenv

import config
from gemini import GeminiSummarization
from notion import NotionScript
from youtube import YoutubeVideoExtractor

load_dotenv()


def setup_logging():
    LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("myapp.log")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)

    return logger


def main():
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Starting Notion media import workflow")
    logger.info("=" * 60)

    notion_api_key = os.getenv("NOTION_API_KEY")
    if not notion_api_key:
        logger.critical("NOTION_API_KEY missing from environment.")
        sys.exit(1)

    youtube_api_key = os.getenv("GOOGLE_API")
    if not youtube_api_key:
        logger.critical("NOTION_API_KEY missing from environment.")
        sys.exit(1)

    try:
        youtube_processor = YoutubeVideoExtractor(api_key=youtube_api_key)

        youtube_id = "-HOp7_-cxTw"

        youtube_data = youtube_processor.extract_data(youtube_id)

        gemini_processor = GeminiSummarization()

        gemini_data = gemini_processor.summarize_video("prompt.txt", youtube_data)

        full_data = dict(youtube_data)
        full_data.update(gemini_data)

        with open(f"{youtube_id}-full.json", "w", encoding="utf-8") as json_file:
            json.dump(full_data, json_file, indent=4, ensure_ascii=False)

        # with open(f"{youtube_id}-yt.json", "w", encoding="utf-8") as json_file:
        #     json.dump(youtube_data, json_file, indent=4, ensure_ascii=False)

        # with open(f"{youtube_id}-ge.json", "w", encoding="utf-8") as json_file:
        #     json.dump(gemini_data, json_file, indent=4, ensure_ascii=False)

        notion_processor = NotionScript(
            api_key=notion_api_key,
            entities_db_id=config.ENTITIES_DB_ID,
            media_db_id=config.MEDIA_DB_ID,
            snippet_db_id=config.SNIPPETS_DB_ID,
        )

        # input_data = NotionScript.load_data_from_json(config.JSON_FILE_NAME)

        result = notion_processor.create_media(full_data)

        if result:
            logger.info("Workflow completed successfully! Media Page ID: %s", result)
        else:
            logger.error("Workflow finished, but Media Page was not created.")
            sys.exit(1)

    except Exception as e:
        logger.critical("Workflow failed: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
