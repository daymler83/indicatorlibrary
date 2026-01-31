from fastapi import APIRouter
from pydantic import BaseModel
import openai
import os

router = APIRouter()

# Load your API key
openai.api_key = os.getenv("OPENAI_API_KEY")

class TranslationRequest(BaseModel):
    text: str
    target_lang: str  # "ar" or "en"

@router.post("/api/translate")
async def translate_text(req: TranslationRequest):
    """
    Translate a piece of text into Arabic or English using GPT.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Translate the following text into {req.target_lang}."},
                {"role": "user", "content": req.text}
            ],
            temperature=0
        )

        translation = response["choices"][0]["message"]["content"].strip()
        return {"translation": translation}

    except Exception as e:
        print("Translation Error:", e)
        return {"error": str(e)}
