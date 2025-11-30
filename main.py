import json
import logging
import sys

import config
from gemini import GeminiProcessor
from notion import NotionIngester
from youtube import YoutubeExtractor


def setup_logging() -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def validate_config(logger: logging.Logger):
    missing_keys = []
    if not config.NOTION_API_KEY:
        missing_keys.append("NOTION_API_KEY")
    if not config.YOUTUBE_API_KEY:
        missing_keys.append("GOOGLE_API")
    if not config.GEMINI_API_KEY:
        missing_keys.append("GEMINI_API_KEY")

    if missing_keys:
        logger.critical(f"Missing environment variables: {', '.join(missing_keys)}")
        logger.critical("Please check your .env file.")
        sys.exit(1)


def load_youtube_ids(file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        ids = json.load(f)

    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
        raise ValueError(f"File {file_path} must contain a JSON list of strings.")

    return ids


def process_single_video(
    video_id: str,
    youtube: YoutubeExtractor,
    gemini: GeminiProcessor,
    notion: NotionIngester,
    logger: logging.Logger,
):
    try:
        logger.info(f"--- Processing: {video_id} ---")

        youtube_data = youtube.extract_data(video_id)
        if not youtube_data:
            logger.warning(f"Skipping {video_id}: Extraction failed")
            return

        gemini_data = gemini.summarize_video(youtube_data)
        if not gemini_data:
            logger.warning(f"Skipping {video_id}: Summarization failed")
            return

        full_data = {**youtube_data, **gemini_data}

        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = config.OUTPUT_DIR / f"{video_id}-full.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(full_data, f, indent=4, ensure_ascii=False)

        notion.create_media(full_data)

    except Exception as e:
        logger.error(f"Error processing {video_id}: {e}", exc_info=True)


def main():
    logger = setup_logging()
    logger.info("Starting Notion Knowledge Hub Batch Workflow")

    validate_config(logger)

    try:
        youtube_extractor = YoutubeExtractor(api_key=config.YOUTUBE_API_KEY)
        gemini_processor = GeminiProcessor()
        notion_ingester = NotionIngester()

        youtube_ids = load_youtube_ids(config.YOUTUBE_IDS_FILE)
        logger.info(f"Loaded {len(youtube_ids)} videos to process.")

        for video_id in youtube_ids:
            process_single_video(
                video_id, youtube_extractor, gemini_processor, notion_ingester, logger
            )

    except Exception as e:
        logger.critical(f"Fatal Error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Batch workflow finished.")


if __name__ == "__main__":
    main()
