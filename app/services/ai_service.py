import os
import google.generativeai as genai
import json
from dotenv import load_dotenv

load_dotenv()


class AIEngineService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')

    async def generate_content(self, level: str) -> list:
        """
        UML: +generateContent(level: string): list
        GÜNCELLEME: Artık sorunun ağırlığını (weight) da AI belirliyor.
        """
        skill = "Reading"
        cefr_level = "B1"

        # Parsing
        if "-" in level:
            parts = level.split("-")
            cefr_level = parts[0].strip()
            skill = parts[1].strip()
        else:
            cefr_level = level

        word_count = "100" if cefr_level in ["A1", "A2"] else "250"

        base_prompt = (
            f"Generate a {skill} exercise strictly for CEFR Level {cefr_level}. "
            f"Use vocabulary/grammar for {cefr_level}. "
            f"Return strict JSON."
        )

        # --- BURASI DEĞİŞTİ KRAL ---
        if skill == "Reading":
            prompt = (
                f"{base_prompt} "
                f"Include a 'text' field (approx {word_count} words). "
                f"Include a 'questions' list with 3 items. "
                f"Each question MUST have: "
                f"1. 'question_text', "
                f"2. 'options' (list of 4), "
                f"3. 'correct_answer' (index 0-3), "
                f"4. 'weight' (integer between 10-50 based on difficulty). "  # <-- YENİ EKLENDİ
            )

        elif skill == "Listening":
            prompt = (
                f"{base_prompt} "
                f"Create a spoken script. Include a 'script' field. "
                f"Include a 'questions' list with 3 items. "
                f"Each question MUST have: "
                f"1. 'question_text', "
                f"2. 'options', "
                f"3. 'correct_answer', "
                f"4. 'weight' (integer between 10-50 based on difficulty). "  # <-- YENİ EKLENDİ
            )

        elif skill == "Writing":
            prompt = f"{base_prompt} Provide 'topics' list with 3 essay prompts."

        elif skill == "Speaking":
            prompt = f"{base_prompt} Provide 'topics' list with 3 discussion topics."

        try:
            response = await self.model.generate_content_async(prompt)
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_text)
        except Exception as e:
            print(f"AI Generation Error: {e}")
            return []

    async def evaluate_response(self, text: str) -> float:
        """
        UML: +evaluateResponse(text: string): float
        """
        try:
            data = json.loads(text)
            exam_type = data.get("type", "Unknown")

            # --- WRITING & SPEAKING (AI Puanlar) ---
            if exam_type in ["Writing", "Speaking"]:
                topic = data.get("topic", "")
                student_response = data.get("student_response", "")

                prompt = (
                    f"Act as an English teacher. Evaluate this {exam_type} response based on CEFR standards.\n"
                    f"Topic: {topic}\n"
                    f"Student Response: {student_response}\n"
                    f"Rate it from 0 to 100 based on grammar, vocabulary, and relevance. "
                    f"Return ONLY the numeric score."
                )
                response = await self.model.generate_content_async(prompt)
                return float(response.text.strip())

            # --- READING & LISTENING (Matematik Puanlar) ---
            elif exam_type in ["Reading", "Listening"]:
                user_answers = data.get("user_answers", [])
                correct_answers = data.get("correct_answers", [])
                weights = data.get("weights", [])  # Controller burayı AI'dan gelen verilerle doldurup yollayacak

                if not correct_answers: return 0.0

                # Eğer Controller ağırlık göndermeyi unutursa eşit dağıt (Fallback)
                if not weights or len(weights) != len(correct_answers):
                    weights = [1] * len(correct_answers)

                total_score = 0.0
                max_possible = sum(weights)

                for i in range(len(correct_answers)):
                    if i < len(user_answers) and str(user_answers[i]).strip().upper() == str(
                            correct_answers[i]).strip().upper():
                        total_score += weights[i]

                # 100'lük sisteme çevir
                if max_possible > 0:
                    final_score = (total_score / max_possible) * 100
                    return float(round(final_score, 2))
                else:
                    return 0.0

            else:
                return 0.0

        except Exception as e:
            print(f"Evaluation Error: {e}")
            return 0.0

    async def calculate_overall_cefr(self, scores: list) -> str:
        if not scores: return "A1"
        avg = sum(scores) / len(scores)
        if avg >= 90:
            return "C2"
        elif avg >= 80:
            return "C1"
        elif avg >= 65:
            return "B2"
        elif avg >= 50:
            return "B1"
        elif avg >= 35:
            return "A2"
        return "A1"


ai_service = AIEngineService()