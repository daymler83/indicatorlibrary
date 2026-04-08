from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
import os
from sqlalchemy.orm import Session
from fastapi import Depends

from db import SessionLocal
from routers.translation_cache import get_cached_translation, store_translation

router = APIRouter()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
api_key = os.getenv("OPENAI_API_KEY")

#client = OpenAI(api_key=api_key) if api_key else None

api_key = os.getenv("OPENAI_API_KEY")

client = None
if api_key:
    client = OpenAI(api_key=api_key)

class PageTranslationRequest(BaseModel):
    html: str
    lang: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/api/translate_page")
async def translate_page(req: PageTranslationRequest, db: Session = Depends(get_db)):
    """
    Translate the full HTML page to the requested language.
    GPT MUST preserve all HTML tags and structure.
    """
    try:
        cached = get_cached_translation(db, "html", req.lang, req.html)
        if cached:
            return {"html": cached.translated_text, "cached": True}

        if not client:
            return {"error": "Translation service not configured (missing OPENAI_API_KEY)"}

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

        translated = response.choices[0].message.content
        store_translation(
            db=db,
            translation_type="html",
            target_lang=req.lang,
            source_text=req.html,
            translated_text=translated,
            source_model="gpt-3.5-turbo",
        )
        return {"html": translated, "cached": False}

    except Exception as e:
        print("PAGE TRANSLATION ERROR:", e)
        return {"error": str(e)}
