import os
from typing import List, Optional

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


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


class GeminiSummarization:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def _load_prompt(self, prompt_path):
        with open(prompt_path, "r") as f:
            return f.read()

    def _format_video_content(self, video_data):
        title = video_data.get("title", "Unknown Title")
        description = video_data.get("description", "No description provided.")
        transcript_raw = video_data.get("transcript", [])
        transcript_text = "\n".join(transcript_raw)

        return (
            f"VIDEO TITLE: {title}\n\n"
            f"VIDEO DESCRIPTION & SOURCES:\n{description}\n\n"
            f"TRANSCRIPT CONTENT:\n{transcript_text}"
        )

    def summarize_video(self, prompt_path, video_data):
        system_instruction = self._load_prompt(prompt_path)
        full_content_text = self._format_video_content(video_data)

        final_prompt = f"{system_instruction}\n\nDATA TO PROCESS:\n{full_content_text}"

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=final_prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": SummaryResponse.model_json_schema(),
            },
        )

        try:
            structured_data = SummaryResponse.model_validate_json(response.text)
            return structured_data.model_dump()
        except Exception as e:
            print(f"Error validating response: {e}")
            return None


# if __name__ == "__main__":
#     summarizer = GeminiSummarization()
#     json_file_path = "Dubq7s-5zLU.json"

#     with open(json_file_path, "r", encoding="utf-8") as f:
#         video_data = json.load(f)

#     result = summarizer.summarize_video("prompt.txt", video_data)

#     if result:
#         with open("result.json", "w", encoding="utf-8") as json_file:
#             json.dump(result, json_file, indent=4, ensure_ascii=False)
#     else:
#         print("Failed to generate or validate summary.")
