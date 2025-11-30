import logging
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

import config

logger = logging.getLogger(__name__)


class EventDate(BaseModel):
    human_readable: Optional[str] = Field(
        description="The date as it appears in the text or 'null' if not specific."
    )
    date_start_iso: Optional[str] = Field(description="ISO format start date or null.")
    date_end_iso: Optional[str] = Field(description="ISO format end date or null.")


class ExtractedSnippet(BaseModel):
    context: str = Field(
        description="The specific text or fact extracted from the transcript."
    )
    entities: List[str] = Field(
        description="List of key resources, people, or concepts involved."
    )
    event_date: EventDate


class SummaryResponse(BaseModel):
    full_summary: str = Field(
        description="A comprehensive summary of the transcript in markdown format."
    )
    extracted_snippets: List[ExtractedSnippet]


load_dotenv()


class GeminiProcessor:
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        logger.info("GeminiProcessor initialized.")

        try:
            self.system_instruction = config.PROMPT_FILE.read_text(encoding="utf-8")
            logger.info(f"Loaded system prompt from {config.PROMPT_FILE}")
        except FileNotFoundError:
            logger.critical(f"Prompt file missing: {config.PROMPT_FILE}")
            raise

    def _format_video_content(self, video_data: Dict[str, Any]) -> str:
        title = video_data.get("title", "Unknown Title")
        description = video_data.get("description", "No description provided.")
        transcript_raw = video_data.get("transcript", [])
        transcript_text = (
            "\n".join(transcript_raw)
            if isinstance(transcript_raw, list)
            else str(transcript_raw)
        )

        return (
            f"VIDEO TITLE: {title}\n\n"
            f"VIDEO DESCRIPTION & SOURCES:\n{description}\n\n"
            f"TRANSCRIPT CONTENT:\n{transcript_text}"
        )

    def summarize_video(self, video_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info("Starting Gemini summarization process.")

        try:
            full_content_text = self._format_video_content(video_data)
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    self.system_instruction,
                    "DATA TO PROCESS:",
                    full_content_text,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": SummaryResponse.model_json_schema(),
                },
            )
            logger.info("Received response from Gemini API.")
            structured_data = SummaryResponse.model_validate_json(response.text)
            logger.info("Gemini response validated against Pydantic schema.")
            return structured_data.model_dump()

        except genai.errors.APIError as e:
            logger.error(f"Gemini API Error: {e}", exc_info=True)
            return None

        except Exception as e:
            logger.error(
                f"Error validating or processing Gemini response: {e}", exc_info=True
            )
            return None
