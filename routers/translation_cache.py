import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from models import TranslationCache


def make_cache_key(translation_type: str, target_lang: str, source_text: str) -> str:
    payload = f"{translation_type}:{target_lang}:{source_text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def get_cached_translation(
    db: Session,
    translation_type: str,
    target_lang: str,
    source_text: str,
):
    cache_key = make_cache_key(translation_type, target_lang, source_text)
    return db.query(TranslationCache).filter(TranslationCache.cache_key == cache_key).first()


def store_translation(
    db: Session,
    translation_type: str,
    target_lang: str,
    source_text: str,
    translated_text: str,
    source_model: Optional[str] = None,
):
    cache_key = make_cache_key(translation_type, target_lang, source_text)
    entry = db.query(TranslationCache).filter(TranslationCache.cache_key == cache_key).first()

    if entry:
        entry.translated_text = translated_text
        entry.source_model = source_model
        entry.source_text = source_text
        entry.target_lang = target_lang
        entry.translation_type = translation_type
    else:
        entry = TranslationCache(
            cache_key=cache_key,
            translation_type=translation_type,
            target_lang=target_lang,
            source_text=source_text,
            translated_text=translated_text,
            source_model=source_model,
        )
        db.add(entry)

    db.commit()
    db.refresh(entry)
    return entry
