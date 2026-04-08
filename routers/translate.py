from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
import os
from sqlalchemy.orm import Session
from fastapi import Depends

from db import SessionLocal
from routers.translation_cache import get_cached_translation, store_translation

router = APIRouter()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

class TranslationRequest(BaseModel):
    text: str
    target_lang: str  # "ar" or "en"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/api/translate")
async def translate_text(req: TranslationRequest, db: Session = Depends(get_db)):
    """
    Translate a piece of text into Arabic or English using GPT.
    """
    cached = get_cached_translation(db, "text", req.target_lang, req.text)
    if cached:
        return {"translation": cached.translated_text, "cached": True}

    if not client:
        return {"error": "Translation service not configured (missing OPENAI_API_KEY)"}

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Translate the following text into {req.target_lang}."},
                {"role": "user", "content": req.text}
            ],
            temperature=0
        )

        translation = response.choices[0].message.content.strip()
        store_translation(
            db=db,
            translation_type="text",
            target_lang=req.target_lang,
            source_text=req.text,
            translated_text=translation,
            source_model="gpt-3.5-turbo",
        )
        return {"translation": translation, "cached": False}

    except Exception as e:
        print("Translation Error:", e)
        return {"error": str(e)}
