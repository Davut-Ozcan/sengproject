import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class SpeechToTextService:
    def __init__(self):
        # AIEngine ile aynı key'i kullanır, masrafsızdır.
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')

    async def transcribe(self, audio_data: bytes) -> str:
        """
        GÖREV: FR15 - Sesi metne çevirir.
        GİRDİ: Ses dosyasının binary verisi (blob/bytes).
        ÇIKTI: Yazıya dökülmüş metin (String).
        """
        try:
            # Gemini'ye net bir emir veriyoruz
            prompt = "Transcribe the spoken English in this audio file exactly as it is. Do not summarize, just transcribe."

            # Gemini 1.5 Flash, sesi doğrudan (bytes olarak) alabilir
            response = await self.model.generate_content_async([
                prompt,
                {
                    "mime_type": "audio/mp3",
                    "data": audio_data
                }
            ])

            return response.text.strip()
        except Exception as e:
            print(f"🚨 STT Hatası: {e}")
            return ""


# Tekil nesne
stt_service = SpeechToTextService()