import logging
import requests

logger = logging.getLogger(__name__)

class IntegrationService:
    """
    Mentoris loyihasining O'zbekiston Respublikasi davlat tizimlari 
    (OneID, UzBMB, HEMIS) bilan integratsiyasini ta'minlovchi xizmat.
    Hozirgi bosqich: Tayyorgarlik (Mocking/Simulyatsiya)
    """

    @staticmethod
    def sync_oneid(pinfl: str) -> dict:
        """
        Yagona Identifikatsiya Tizimi (OneID) orqali foydalanuvchi ma'lumotlarini olish.
        Kelajakda haqiqiy OAuth2/SAML integratsiyasiga ulanadi.
        """
        logger.info(f"OneID so'rovi yuborildi: PINFL {pinfl}")
        return {
            "success": True,
            "data": {
                "full_name": "TOSHPULATOV ESHMAT TOSHPULATOVICH",
                "pinfl": pinfl,
                "verified": True
            }
        }

    @staticmethod
    def get_uzbmb_results(passport_number: str) -> dict:
        """
        UzBMB (DTM) orqali abituriyentning imtihon natijalari va o'tish ballari arxivini tortish.
        """
        logger.info(f"UzBMB so'rovi yuborildi: Passport {passport_number}")
        return {
            "success": True,
            "data": {
                "score": 156.4,
                "university": "Toshkent Axborot Texnologiyalari Universiteti",
                "status": "grant"
            }
        }

    @staticmethod
    def get_hemis_data(student_id: str) -> dict:
        """
        HEMIS tizimi orqali talabaning GPA, davomat va fanlarni o'zlashtirish darajasini tortish.
        """
        logger.info(f"HEMIS so'rovi yuborildi: ID {student_id}")
        return {
            "success": True,
            "data": {
                "gpa": 4.2,
                "semester": 5,
                "debts": 0
            }
        }
