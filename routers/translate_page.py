from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
import os

router = APIRouter()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key) if api_key else None

class PageTranslationRequest(BaseModel):
    html: str
    lang: str

@router.post("/api/translate_page")
async def translate_page(req: PageTranslationRequest):
    """
    Translate the full HTML page to the requested language.
    GPT MUST preserve all HTML tags and structure.
    """
    try:
        prompt = (
            f"Translate all visible UI text in the following HTML into {req.lang}. "
            f"Do NOT change any HTML tags, attributes, class names, IDs, scripts, or structure. "
            f"Translate only human-readable text.\n\n"
            f"{req.html}"
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or gpt-3.5-turbo if you prefer
            messages=[
                {"role": "system", "content": "You translate HTML UI text while preserving all markup intact."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        translated = response.choices[0].message["content"]
        return {"html": translated}

    except Exception as e:
        print("PAGE TRANSLATION ERROR:", e)
        return {"error": str(e)}
