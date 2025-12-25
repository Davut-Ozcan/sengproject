import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class AIEngineService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-flash-latest")

    # ---------------------------
    # JSON helper'lar
    # ---------------------------
    def _strip_code_fences(self, text: str) -> str:
        t = text.strip()
        # ```json ... ``` veya ``` ... ``` temizle
        t = re.sub(r"^\s*```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
        return t.strip()

    def _extract_json_object(self, text: str) -> str:
        """
        Model bazen JSON öncesi/sonrası açıklama koyuyor.
        İlk '{' ile son '}' arasını almayı dener.
        """
        t = text.strip()
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            return t[start : end + 1]
        return t

    def _remove_trailing_commas(self, text: str) -> str:
        # ,] ve ,} gibi trailing comma'ları temizle
        return re.sub(r",\s*([\]}])", r"\1", text)

    def _safe_json_loads(self, raw_text: str):
        """
        Sadece JSON parse. Olmazsa hata fırlatır.
        """
        t = self._strip_code_fences(raw_text)
        t = self._extract_json_object(t)
        t = self._remove_trailing_commas(t)
        return json.loads(t)

    async def generate_content(self, level: str) -> dict:
        """
        UML: +generateContent(level: string): dict
        AI içerik üretir. JSON döndürür.
        """

        if not self.model:
            print("AI Generation Error: GEMINI_API_KEY is missing or model not initialized.")
            return {}

        # Default parameters
        skill = "Reading"
        cefr_level = "B1"

        # Parsing (ex: A1-Listening)
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
            f"Return strict JSON only. No markdown. No extra text."
        )

        if skill == "Reading":
            prompt = (
                f"{base_prompt} "
                f"Include a 'text' field (approx {word_count} words). "
                f"Include a 'questions' list with 3 items. "
                f"Each question MUST have: "
                f"'question_text', "
                f"'options' (list of 4 strings), "
                f"'correct_answer' (index 0-3 as integer), "
                f"'weight' (integer between 10-50)."
            )

        elif skill == "Listening":
            prompt = (
                f"{base_prompt} "
                f"Create a spoken script. Include a 'script' field. "
                f"Include a 'questions' list with 3 items. "
                f"Each question MUST have: "
                f"'question_text', "
                f"'options' (list of 4 strings), "
                f"'correct_answer' (index 0-3 as integer), "
                f"'weight' (integer between 10-50)."
            )

        elif skill == "Writing":
            # Örnek formatı mutlaka çift tırnakla veriyoruz (tek tırnak JSON değil)
            prompt = (
                f"{base_prompt} "
                f"The response MUST be a valid JSON object with a single key \"topics\". "
                f"The value must be a list of 3 strings. "
                f"Example: {{\"topics\": [\"Discuss the benefits of technology.\", "
                f"\"Is tourism good for local economy?\", "
                f"\"Describe a memorable event.\"]}}"
            )

        elif skill == "Speaking":
            prompt = (
                f"{base_prompt} "
                f"The response MUST be a valid JSON object with a single key \"topics\". "
                f"The value must be a list of 3 discussion questions. "
                f"Example: {{\"topics\": [\"What are your hobbies?\", "
                f"\"Describe your hometown.\", "
                f"\"Do you prefer summer or winter?\"]}}"
            )

        else:
            # Bilinmeyen skill gelirse safe fallback
            prompt = base_prompt + " Return an empty JSON object {}."

        try:
            response = await self.model.generate_content_async(prompt)
            raw_text = (response.text or "").strip()

            # Önce sağlam parse dene
            data = self._safe_json_loads(raw_text)

            # Minimum doğrulama (boş gelmesin)
            if not isinstance(data, dict):
                print("AI Generation Error: Parsed JSON is not an object/dict.")
                print("RAW AI OUTPUT:", raw_text)
                return {}

            return data

        except Exception as e:
            print(f"AI Generation Error: {e}")
            try:
                # Parse patladıysa ham output'u logla (debug için altın)
                raw_text = (response.text or "").strip()  # type: ignore[name-defined]
                print("RAW AI OUTPUT:", raw_text)
            except Exception:
                pass
            return {}

    async def evaluate_response(self, text: str) -> float:
        """
        UML: +evaluateResponse(text: string): float
        """
        if not self.model:
            print("Evaluation Error: model not initialized.")
            return 0.0

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
                weights = data.get("weights", [])

                if not correct_answers:
                    return 0.0

                if not weights or len(weights) != len(correct_answers):
                    weights = [1] * len(correct_answers)

                total_score = 0.0
                max_possible = sum(weights)

                for i in range(len(correct_answers)):
                    if i < len(user_answers) and str(user_answers[i]).strip().upper() == str(
                        correct_answers[i]
                    ).strip().upper():
                        total_score += weights[i]

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
        """
        UML: +calculateOverallCEFR(scores: list): string
        """
        if not scores:
            return "A1"

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
        else:
            return "A1"


ai_service = AIEngineService()
