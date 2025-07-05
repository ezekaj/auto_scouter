"""
Internationalization API Router

This module provides API endpoints for language management and translations.
"""

from fastapi import APIRouter, Request, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

from app.core.i18n import translation_service, SupportedLanguage, translate
from app.middleware.i18n_middleware import get_request_language

router = APIRouter()


class LanguageInfo(BaseModel):
    """Language information model"""
    code: str
    name: str
    native_name: str
    flag: str


class TranslationResponse(BaseModel):
    """Translation response model"""
    language: str
    translations: Dict[str, str]


@router.get("/languages", response_model=List[LanguageInfo])
async def get_supported_languages():
    """Get list of supported languages"""
    return [
        LanguageInfo(
            code="sq",
            name="Albanian",
            native_name="Shqip",
            flag="🇦🇱"
        ),
        LanguageInfo(
            code="it",
            name="Italian",
            native_name="Italiano",
            flag="🇮🇹"
        )
    ]


@router.get("/current-language")
async def get_current_language(request: Request):
    """Get current detected language"""
    language = get_request_language(request)
    
    language_info = {
        SupportedLanguage.ALBANIAN: {
            "code": "sq",
            "name": "Albanian",
            "native_name": "Shqip",
            "flag": "🇦🇱"
        },
        SupportedLanguage.ITALIAN: {
            "code": "it",
            "name": "Italian",
            "native_name": "Italiano",
            "flag": "🇮🇹"
        }
    }
    
    return {
        "detected_language": language.value,
        "language_info": language_info[language],
        "message": translate("data_retrieved", language)
    }


@router.get("/translations/{language_code}", response_model=TranslationResponse)
async def get_translations(language_code: str):
    """Get all translations for a specific language"""
    try:
        language = SupportedLanguage(language_code)
    except ValueError:
        language = SupportedLanguage.ALBANIAN
    
    translations = translation_service.translations.get(language, {})
    
    return TranslationResponse(
        language=language.value,
        translations=translations
    )


@router.get("/translate/{key}")
async def translate_key(key: str, request: Request, language_code: str = None):
    """Translate a specific key"""
    if language_code:
        try:
            language = SupportedLanguage(language_code)
        except ValueError:
            language = get_request_language(request)
    else:
        language = get_request_language(request)
    
    translation = translate(key, language)
    
    return {
        "key": key,
        "language": language.value,
        "translation": translation,
        "original": key if translation == key else None
    }


@router.post("/test-translation")
async def test_translation(request: Request):
    """Test translation functionality with sample data"""
    language = get_request_language(request)
    
    # Sample data to translate
    sample_data = {
        "message": "login_success",
        "detail": "operation_completed",
        "error": None,
        "data": {
            "status": "success",
            "count": 5
        }
    }
    
    # Translate the response
    translated_data = translation_service.translate_response(sample_data, language)
    
    return {
        "detected_language": language.value,
        "original_data": sample_data,
        "translated_data": translated_data,
        "available_languages": translation_service.get_supported_languages()
    }


@router.get("/health")
async def i18n_health():
    """Get i18n system health status"""
    return {
        "status": "healthy",
        "supported_languages": translation_service.get_supported_languages(),
        "total_translations": {
            lang.value: len(translations)
            for lang, translations in translation_service.translations.items()
        },
        "message": "I18n system is operational"
    }
