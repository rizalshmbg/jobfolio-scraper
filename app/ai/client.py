from google import genai

from ..core.config import settings


class GeminiClient:
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def generate_text(
        self,
        prompt: str,
    ) -> str:
        response = self.client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
        )

        return response.text or ""
