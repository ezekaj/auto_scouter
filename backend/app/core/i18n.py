"""
Internationalization (i18n) support for the backend

This module provides translation support for Albanian and Italian languages
for API responses, email templates, and other backend messages.
"""

from typing import Dict, Any, Optional
from enum import Enum


class SupportedLanguage(str, Enum):
    """Supported languages"""
    ALBANIAN = "sq"
    ITALIAN = "it"


class TranslationService:
    """Service for handling translations in the backend"""
    
    def __init__(self):
        self.translations = {
            SupportedLanguage.ALBANIAN: {
                # Common messages
                "success": "Sukses",
                "error": "Gabim",
                "not_found": "Nuk u gjet",
                "unauthorized": "I paautorizuar",
                "forbidden": "I ndaluar",
                "validation_error": "Gabim validimi",
                "server_error": "Gabim në server",
                
                # Authentication
                "login_success": "Hyrja u krye me sukses",
                "login_failed": "Hyrja dështoi",
                "logout_success": "Dalja u krye me sukses",
                "registration_success": "Regjistrimi u krye me sukses",
                "registration_failed": "Regjistrimi dështoi",
                "invalid_credentials": "Kredencialet janë të gabuara",
                "token_expired": "Token-i ka skaduar",
                "token_invalid": "Token-i është i pavlefshëm",
                
                # Vehicle related
                "vehicle_not_found": "Automjeti nuk u gjet",
                "vehicle_saved": "Automjeti u ruajt",
                "vehicle_updated": "Automjeti u përditësua",
                "vehicle_deleted": "Automjeti u fshi",
                "search_results": "Rezultatet e kërkimit",
                "no_vehicles_found": "Nuk u gjetën automjete",
                
                # Alerts
                "alert_created": "Alarmi u krijua",
                "alert_updated": "Alarmi u përditësua",
                "alert_deleted": "Alarmi u fshi",
                "alert_triggered": "Alarmi u aktivizua",
                "alert_not_found": "Alarmi nuk u gjet",
                
                # Notifications
                "notification_sent": "Njoftimi u dërgua",
                "notification_failed": "Njoftimi dështoi",
                "email_sent": "Email-i u dërgua",
                "email_failed": "Email-i dështoi",
                
                # Email templates
                "welcome_subject": "Mirë se vini në Auto Scouter",
                "welcome_body": "Mirë se vini në platformën tonë të kërkimit të automjeteve!",
                "alert_subject": "Alarm i ri për automjetin tuaj",
                "alert_body": "Gjetëm një automjet që përputhet me kriteret tuaja.",
                "password_reset_subject": "Rivendosja e fjalëkalimit",
                "password_reset_body": "Klikoni këtu për të rivendosur fjalëkalimin tuaj.",
                
                # API responses
                "data_retrieved": "Të dhënat u morën me sukses",
                "data_saved": "Të dhënat u ruajtën me sukses",
                "data_updated": "Të dhënat u përditësuam me sukses",
                "data_deleted": "Të dhënat u fshinë me sukses",
                "operation_completed": "Operacioni u përfundua me sukses",
                "operation_failed": "Operacioni dështoi",
                
                # Validation messages
                "field_required": "Fusha është e detyrueshme",
                "invalid_email": "Email-i është i pavlefshëm",
                "password_too_short": "Fjalëkalimi është shumë i shkurtër",
                "passwords_dont_match": "Fjalëkalimet nuk përputhen",
                "invalid_format": "Formati është i pavlefshëm",
                "value_too_large": "Vlera është shumë e madhe",
                "value_too_small": "Vlera është shumë e vogël",
            },
            
            SupportedLanguage.ITALIAN: {
                # Common messages
                "success": "Successo",
                "error": "Errore",
                "not_found": "Non trovato",
                "unauthorized": "Non autorizzato",
                "forbidden": "Vietato",
                "validation_error": "Errore di validazione",
                "server_error": "Errore del server",
                
                # Authentication
                "login_success": "Accesso effettuato con successo",
                "login_failed": "Accesso fallito",
                "logout_success": "Uscita effettuata con successo",
                "registration_success": "Registrazione completata con successo",
                "registration_failed": "Registrazione fallita",
                "invalid_credentials": "Credenziali non valide",
                "token_expired": "Token scaduto",
                "token_invalid": "Token non valido",
                
                # Vehicle related
                "vehicle_not_found": "Veicolo non trovato",
                "vehicle_saved": "Veicolo salvato",
                "vehicle_updated": "Veicolo aggiornato",
                "vehicle_deleted": "Veicolo eliminato",
                "search_results": "Risultati della ricerca",
                "no_vehicles_found": "Nessun veicolo trovato",
                
                # Alerts
                "alert_created": "Avviso creato",
                "alert_updated": "Avviso aggiornato",
                "alert_deleted": "Avviso eliminato",
                "alert_triggered": "Avviso attivato",
                "alert_not_found": "Avviso non trovato",
                
                # Notifications
                "notification_sent": "Notifica inviata",
                "notification_failed": "Notifica fallita",
                "email_sent": "Email inviata",
                "email_failed": "Email fallita",
                
                # Email templates
                "welcome_subject": "Benvenuto in Auto Scouter",
                "welcome_body": "Benvenuto nella nostra piattaforma di ricerca veicoli!",
                "alert_subject": "Nuovo avviso per il tuo veicolo",
                "alert_body": "Abbiamo trovato un veicolo che corrisponde ai tuoi criteri.",
                "password_reset_subject": "Reimpostazione password",
                "password_reset_body": "Clicca qui per reimpostare la tua password.",
                
                # API responses
                "data_retrieved": "Dati recuperati con successo",
                "data_saved": "Dati salvati con successo",
                "data_updated": "Dati aggiornati con successo",
                "data_deleted": "Dati eliminati con successo",
                "operation_completed": "Operazione completata con successo",
                "operation_failed": "Operazione fallita",
                
                # Validation messages
                "field_required": "Il campo è obbligatorio",
                "invalid_email": "Email non valida",
                "password_too_short": "Password troppo corta",
                "passwords_dont_match": "Le password non corrispondono",
                "invalid_format": "Formato non valido",
                "value_too_large": "Valore troppo grande",
                "value_too_small": "Valore troppo piccolo",
            }
        }
    
    def get_translation(self, key: str, language: SupportedLanguage = SupportedLanguage.ALBANIAN) -> str:
        """Get translation for a key in the specified language"""
        try:
            return self.translations[language].get(key, key)
        except KeyError:
            # Fallback to Albanian if language not found
            return self.translations[SupportedLanguage.ALBANIAN].get(key, key)
    
    def translate_response(self, response_data: Dict[str, Any], language: SupportedLanguage = SupportedLanguage.ALBANIAN) -> Dict[str, Any]:
        """Translate response data based on language"""
        if isinstance(response_data, dict):
            translated = {}
            for key, value in response_data.items():
                if key in ["message", "detail", "error"]:
                    # Try to translate common message keys
                    translated[key] = self.get_translation(value, language)
                else:
                    translated[key] = value
            return translated
        return response_data
    
    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes"""
        return [lang.value for lang in SupportedLanguage]


# Global translation service instance
translation_service = TranslationService()


def get_user_language(accept_language: Optional[str] = None) -> SupportedLanguage:
    """Determine user language from Accept-Language header or default to Albanian"""
    if accept_language:
        # Parse Accept-Language header
        languages = accept_language.lower().split(',')
        for lang in languages:
            lang_code = lang.split(';')[0].strip()
            if lang_code.startswith('sq'):
                return SupportedLanguage.ALBANIAN
            elif lang_code.startswith('it'):
                return SupportedLanguage.ITALIAN
    
    # Default to Albanian
    return SupportedLanguage.ALBANIAN


def translate(key: str, language: Optional[SupportedLanguage] = None) -> str:
    """Convenience function for translation"""
    if language is None:
        language = SupportedLanguage.ALBANIAN
    return translation_service.get_translation(key, language)


def translate_response(response_data: Dict[str, Any], language: Optional[SupportedLanguage] = None) -> Dict[str, Any]:
    """Convenience function for response translation"""
    if language is None:
        language = SupportedLanguage.ALBANIAN
    return translation_service.translate_response(response_data, language)
