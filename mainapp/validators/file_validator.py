import os
import magic
from django.core.exceptions import ValidationError

# Ruxsat etilgan MIME turlari
ALLOWED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
}

# Maksimal hajm: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_user_document(file):
    """
    Chuqur fayl tahlili: hajm, kengaytma va MIME turi tekshiruvi.
    """
    # 1. Hajmni tekshirish
    if file.size > MAX_FILE_SIZE:
        raise ValidationError("Fayl hajmi juda katta (Maksimal 5MB ruxsat etilgan).")

    # 2. Kengaytmani tekshirish
    ext = os.path.splitext(file.name)[1].lower()
    
    # 3. MIME turini tekshirish (Magic bytes)
    try:
        # Faylning boshidan bir qismini o'qiymiz
        file_content = file.read(2048)
        file.seek(0) # Kursorni qaytarib qo'yamiz
        
        mime_type = magic.from_buffer(file_content, mime=True)
        
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(f"Noma'lum fayl turi: {mime_type}. Faqat PDF, DOCX va TXT ruxsat etilgan.")
        
        # MIME turi va kengaytma mosligini tekshiramiz
        if ALLOWED_MIME_TYPES[mime_type] != ext:
            raise ValidationError("Fayl kengaytmasi uning mazmuniga mos kelmaydi.")
            
    except Exception as e:
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"Faylni tahlil qilishda xatolik yuz berdi: {str(e)}")

    return True
