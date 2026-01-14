from gtts import gTTS
import os
import uuid


class TextToSpeechService:
    def convert_text_to_audio(self, text: str, slow: bool = False) -> str:
        """
        GÖREV: FR32 & FR1183 - Metni sese çevirir.
        GİRDİ: Okunacak metin (Script) ve Hız Ayarı (slow).
        ÇIKTI: Oluşturulan ses dosyasının yolu (Path).
        """
        try:
            if not text:
                print("TTS Hatası: Metin boş geldi.")
                return ""

            # 1. Ses dosyasını oluştur (Google Translate API kullanır)
            # DÜZELTME: Artık dışarıdan gelen 'slow' parametresini kullanıyoruz.
            tts = gTTS(text=text, lang='en', slow=slow)

            # 2. Kayıt Klasörünü Ayarla
            # Web projelerinde genelde 'static' klasörü dışarıya açıktır.
            # Not: Windows/Linux yol farkı olmaması için os.path kullanıyoruz.
            output_folder = os.path.join("static", "audio")
            os.makedirs(output_folder, exist_ok=True)  # Klasör yoksa oluşturur

            # 3. Benzersiz Dosya İsmi Üret (listening_a1b2c3d4.mp3 gibi)
            filename = f"listening_{uuid.uuid4().hex[:8]}.mp3"
            file_path = os.path.join(output_folder, filename)

            # 4. Kaydet
            tts.save(file_path)
            print(f"✅ Ses dosyası oluşturuldu: {file_path}")

            # Frontend'e veya Controller'a dosya yolunu dönüyoruz
            return file_path

        except Exception as e:
            print(f"🚨 TTS Kritik Hata: {e}")
            return ""


# Tekil nesne (Singleton)
tts_service = TextToSpeechService()