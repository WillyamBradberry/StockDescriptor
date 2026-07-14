import base64
import json
import os
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from pipeline.lm_studio_client import LMStudioClient


load_dotenv()  # Загружает переменные окружения из .env файла (например, GEMINI_API_KEY)

class LLMProvider:
    """Универсальный LLM-провайдер для Gemini и LM Studio."""

    def __init__(self, config: dict):
        self.config = config

    # ── Утилиты ─────────────────────────────────────────────────────

    @staticmethod
    def _encode_image(image_path: str, max_size: int = 1024) -> tuple[str, str]:
        """Кодирует изображение в base64."""
        img = Image.open(image_path)
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        ext = os.path.splitext(image_path)[1].lower()
        fmt = "PNG" if ext == ".png" else "JPEG"
        mime = "image/png" if ext == ".png" else "image/jpeg"

        buf = BytesIO()
        img.save(buf, format=fmt, quality=85)
        return base64.b64encode(buf.getvalue()).decode("utf-8"), mime

    @staticmethod
    def _clean_markdown_block(text: str) -> str:
        """Убирает markdown-код-блоки из ответа LLM."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            text = "\n".join(lines).strip()
        return text

    @staticmethod
    def _strip_thinking_content(text: str) -> str:
        """Вырезает thinking/reasoning контент из ответа модели.

        Модель Qwen3 часто выводит thinking process даже при reasoning=False:
        - "Here's a thinking process:\n1. **Analyze User Input:**..." до </think>
        - Может выдать голый </think> без открывающего тега
        - Внутри thinking process могут встречаться [Section Headers] (например,
          [Composition & Scene]), поэтому искать первый '[' — недостаточно.

        Алгоритм:
        1. Удалить <think>...</think> блоки
        2. Удалить сиротский </think>
        3. Удалить явные преамбулы типа "Here's a thinking process:"
        4. Найти первый '[' (начало JSON массива) или '{' (начало JSON объекта)
        5. Если ничего не найдено — вернуть текст как есть
        """
        if not text:
            return text

        import re

        # 1. Удаляем <think>...</think> блоки и сиротский </think>
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = text.replace('</think>', '')

        # 2. Удаляем "Here's a thinking process:" и подобные преамбулы
        #    до первого вхождения JSON-подобной структуры
        text = re.sub(
            r"Here's a thinking process:.*?(?=\[\s*\{)",
            '',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(
            r"Here's a thinking process:.*?(?=\s*\[)",
            '',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # 3. Удаляем любые другие преамбулы до JSON
        #    Ищем паттерны вроде "I'll analyze...", "Let me think...", etc.
        text = re.sub(
            r"(?:I'll|Let me|Let's|I will|I need to|Okay|Alright|Sure|Here is|Here's).+?(?=\[\s*\{|\s*\[)",
            '',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # 4. Ищем начало JSON: либо '[', либо '{'
        #    Важно: ищем именно начало JSON массива/объекта, а не секционные заголовки
        best_idx = -1

        # Ищем '{' (начало JSON объекта)
        brace_idx = text.find('{')
        if brace_idx != -1:
            best_idx = brace_idx

        # Ищем '[' (начало JSON массива)
        # Находим ВСЕ вхождения '[' и проверяем, является ли каждое началом JSON
        for m in re.finditer(r'\[', text):
            pos = m.start()
            # Проверяем, не похож ли этот '[' на секционный заголовок внутри промпта
            # Секционные заголовки: [Something - Something] или [Something]:
            rest = text[pos + 1:pos + 50]  # Берём первые 50 символов после '['
            section_match = re.match(
                r'(?:Composition|Subject|Enemies|Art Style|Lighting|Colors?|Core Subject|Background)\s*[\-&]',
                rest,
                re.IGNORECASE,
            )
            if not section_match:
                # Это похоже на начало JSON массива
                if best_idx == -1 or pos < best_idx:
                    best_idx = pos
                break  # Берём первое подходящее вхождение

        if best_idx != -1:
            return text[best_idx:].strip()

        # 5. Fallback: если JSON не найден, но есть '[' или '{'
        fallback_idx = text.find('[')
        if fallback_idx != -1:
            return text[fallback_idx:].strip()

        fallback_idx = text.find('{')
        if fallback_idx != -1:
            return text[fallback_idx:].strip()

        return text

    def _get_lm_studio_chat_url(self) -> str:
        """Собирает правильный URL для /v1/chat/completions LM Studio."""
        base = str(self.config.get("lm_studio_api_url", "http://127.0.0.1:1234/v1")).rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"

    def _get_lm_studio_client(self) -> LMStudioClient:
        return LMStudioClient(
            base_url=self.config.get("lm_studio_api_url", "http://127.0.0.1:1234"),
            launch_path=self.config.get("lm_studio_path") if self.config.get("auto_start_lm_studio", True) else None,
        )

    def _is_lm_studio_available(self, timeout: int = 5) -> bool:
        try:
            health = requests.get(
                str(self.config.get("lm_studio_api_url", "http://127.0.0.1:1234")).rstrip("/v1") + "/v1/models",
                timeout=timeout,
            )
            return health.status_code == 200
        except Exception:
            return False

    def _ensure_lm_studio_available(self, timeout: int = 60) -> bool:
        client = self._get_lm_studio_client()
        return client.ensure_available(timeout=timeout)

    # ── Gemini: текст ───────────────────────────────────────────────

    def _call_gemini_text(self, system_instruction: str, prompt: str) -> str | None:
        """Отправляет текстовый запрос в Gemini API."""
        model = str(self.config.get("gemini_model", "gemini-2.5-flash")).strip()
        # api_key = str(self.config.get("gemini_api_key", "")).strip()
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            print("[-] Gemini API key не указан в config.json")
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_instruction}\n\nUser Request: {prompt}"}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "maxOutputTokens": int(self.config.get("gemini_max_output_tokens", 32768)),
                "temperature": 0.7
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            res_json = response.json()
            if "candidates" not in res_json:
                print(f"[-] Ошибка Gemini API: {json.dumps(res_json, ensure_ascii=False)}")
                return None
            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return text
        except Exception as e:
            print(f"[-] Исключение Gemini API: {e}")
            return None

    # ── Gemini: Vision ──────────────────────────────────────────────

    def _call_gemini_vision(self, image_path: str, system_instruction: str) -> str | None:
        """Отправляет изображение в Gemini Vision API."""
        model = str(self.config.get("gemini_vision_model") or self.config.get("gemini_model", "gemini-2.5-flash")).strip()
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            print("[-] Gemini API key не указан в .env (GEMINI_API_KEY)")
            return None

        b64_image, mime = self._encode_image(image_path)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [
                    {"text": system_instruction},
                    {"inline_data": {"mime_type": mime, "data": b64_image}}
                ]
            }]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            res_json = response.json()
            if "candidates" not in res_json:
                print(f"[-] Ошибка Gemini Vision API: {json.dumps(res_json, ensure_ascii=False)}")
                return None
            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return self._clean_markdown_block(text)
        except Exception as e:
            print(f"[-] Исключение Gemini Vision API: {e}")
            return None

    # ── LM Studio: текст ────────────────────────────────────────────

    def _call_lm_studio_text(self, system_instruction: str, prompt: str, force_no_reasoning: bool = False) -> str | None:
        """Отправляет текстовый запрос в LM Studio.

        КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: для storyboard generation reasoning ОТКЛЮЧАЕТСЯ
        принудительно, т.к. он съедает 60-70% контекста и приводит к обрыву JSON.
        """
        url = self._get_lm_studio_chat_url()
        model = str(self.config.get("lm_studio_model", "qwen3.6-35b-a3b")).strip()

        # ПРИНУДИТЕЛЬНО отключаем reasoning для storyboard — он бесполезен и вреден
        use_reasoning = self.config.get('providers', {}).get('use_reasoning', True)
        if force_no_reasoning:
            use_reasoning = False
            print("[~] Reasoning принудительно отключён для storyboard generation")

        def _do_request(enable_reasoning: bool) -> tuple[str | None, str | None]:
            """Отправляет запрос. Возвращает (content, finish_reason)."""
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                # УВЕЛИЧИЛИ max_tokens: 32000 для reasoning (лимит модели), 24000 без
                "max_tokens": int(self.config.get(
                    "lm_studio_max_tokens_reasoning" if enable_reasoning else "lm_studio_max_tokens",
                    32000 if enable_reasoning else 24000,
                )),
            }
            if not enable_reasoning:
                payload["reasoning"] = False

            headers = {"Content-Type": "application/json"}
            print(f"[~] Запрос к LM Studio (модель: {model}, reasoning: {enable_reasoning})...")
            if enable_reasoning:
                print("[~] Модель использует глубокое рассуждение (Reasoning). Ожидание может занять пару минут...")

            try:
                response = requests.post(url, headers=headers, json=payload, timeout=300)
                res_json = response.json()

                if "choices" not in res_json:
                    print(f"[-] Неверный формат ответа LM Studio: {json.dumps(res_json, ensure_ascii=False)}")
                    return None, None

                finish_reason = str(res_json["choices"][0].get("finish_reason", "")).strip()
                msg = res_json["choices"][0]["message"]
                content = msg.get("content", "").strip()

                return content if content else None, finish_reason
            except Exception as e:
                print(f"[-] Ошибка при вызове LM Studio: {e}")
                return None, None

        # --- Первая попытка (с reasoning, если включён) ---
        content, finish_reason = _do_request(use_reasoning)

        if content:
            cleaned = self._strip_thinking_content(content)
            if cleaned:
                return cleaned
            return content

        # Если ответ пуст из-за нехватки токенов — пробуем без reasoning
        if use_reasoning and finish_reason == "length":
            print("[!] Reasoning съел все токены, ответ не сгенерирован. "
                  "Пробую повторный запрос БЕЗ reasoning...")
            content, finish_reason2 = _do_request(enable_reasoning=False)

            if content:
                print("[+] Повторный запрос без reasoning успешен.")
                cleaned = self._strip_thinking_content(content)
                return cleaned if cleaned else content

            if finish_reason2 == "length":
                print("[-] Даже без reasoning ответ не помещается в контекст модели. "
                      "Сократите входные данные или используйте модель с большим контекстом.")
            else:
                print(f"[-] Повторный запрос без reasoning не дал результата (finish_reason: {finish_reason2}).")
            return None

        # Другие причины пустого ответа
        if finish_reason == "length":
            print("[-] Модель не успела сгенерировать ответ (достигнут лимит токенов). "
                  "Попробуйте отключить reasoning в config.json или сократить входные данные.")
        elif finish_reason == "stop":
            print("[-] Модель вернула пустой ответ при finish_reason='stop'. "
                  "Возможно, модель не справилась с задачей.")
        else:
            print(f"[-] Модель вернула пустой ответ (finish_reason: {finish_reason})")
        return None

    # ── LM Studio: Vision ───────────────────────────────────────────

    def _call_lm_studio_vision(self, image_path: str, system_instruction: str) -> str | None:
        """Отправляет изображение в Vision-модель LM Studio."""
        url = self._get_lm_studio_chat_url()
        model = str(self.config.get("lm_studio_model", "qwen3.6-35b-a3b")).strip()
        if not self._is_lm_studio_available(timeout=2):
            if self.config.get("auto_start_lm_studio", True):
                print("[LM Studio] Сервер недоступен. Пытаюсь автозапустить...")
                if not self._ensure_lm_studio_available(timeout=60):
                    print("[-] Не удалось запустить LM Studio автоматически.")
                    return None
                print("[LM Studio] Сервер запущен.")
            else:
                print("[-] LM Studio не запущен и автостарта отключён.")
                return None
        try:
            health = requests.get(f"{self.config.get('lm_studio_api_url', 'http://127.0.0.1:1234/v1').rstrip('/v1')}/v1/models", timeout=5)
            if health.status_code != 200:
                print("[-] LM Studio не запущен или недоступен.")
                return None
            available = [m.get("id", "") for m in health.json().get("data", [])]
            if model not in available:
                print(f"[-] Модель {model} не найдена среди загруженных в LM Studio: {available}")
                return None
        except Exception as e:
            print(f"[-] LM Studio недоступен: {e}")
            return None

        if not os.path.exists(image_path):
            print(f"[-] Файл изображения не найден: {image_path}")
            return None

        b64_image, mime = self._encode_image(image_path)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this image and provide the optimized prompt:"},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_image}"}}
                    ]
                }
            ],
            "temperature": 0.7,
            "max_tokens": int(self.config.get("lm_studio_max_tokens_vision", 4096)),
        }

        headers = {"Content-Type": "application/json"}
        print(f"[~] Отправка Vision-запроса в LM Studio (модель: {model})...")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=600)
            if response.status_code != 200:
                print(f"[-] Ошибка Vision API LM Studio: {response.status_code} - {response.text}")
                return None

            msg = response.json()["choices"][0]["message"]
            content = msg.get("content", "").strip()
            if not content:
                print("[-] Vision-модель вернула пустой content.")
                return None
            return self._clean_markdown_block(content)
        except Exception as e:
            print(f"[-] Ошибка Vision-запроса LM Studio: {e}")
            return None

    # ── Публичные методы ────────────────────────────────────────────

    def generate_text(self, system_instruction: str, prompt: str) -> str | None:
        """Генерирует текст. Для storyboard ПРИНУДИТЕЛЬНО отключает reasoning."""
        provider = self.config.get("providers", {}).get("text_generation", "gemini")
        use_fallback = provider == "gemini_fallback"

        # Определяем, это storyboard generation или нет
        # Heuristic: если в prompt есть "shot" или "scene" — это storyboard
        is_storyboard = any(kw in prompt.lower() for kw in ["shot", "scene", "storyboard", "кадр"])
        force_no_reasoning = is_storyboard  # ПРИНУДИТЕЛЬНО отключаем для storyboard

        if provider == "gemini" or use_fallback:
            print("[+] Используется Gemini API (текст)...")
            result = self._call_gemini_text(system_instruction, prompt)
            if result:
                return result
            if not use_fallback:
                print("[-] Gemini не ответил. Отключите Gemini в config.json или переключитесь на gemini_fallback.")
                return None
            print("[~] Gemini не ответил (ошибка/недоступен). Переключаюсь на LM Studio...")

        if provider == "lm_studio" or use_fallback:
            print("[+] Используется LM Studio (текст)...")
            if not self._is_lm_studio_available(timeout=2):
                # Пропускаем автозапуск — PromptRefactorer уже сделал это выше
                print("[-] LM Studio не доступен. Убедитесь, что сервер запущен.")
                if not use_fallback:
                    return None
            result = self._call_lm_studio_text(system_instruction, prompt, force_no_reasoning=force_no_reasoning)
            if result:
                return result

        if use_fallback:
            print("[-] Оба провайдера (Gemini и LM Studio) не дали результата.")

        return None

    def analyze_image(self, image_path: str, system_instruction: str) -> str | None:
        """Анализирует изображение."""
        provider = self.config.get("providers", {}).get("vision_analysis", "lm_studio")

        if provider == "gemini":
            print("[+] Используется Gemini Vision API...")
            return self._call_gemini_vision(image_path, system_instruction)
        elif provider == "lm_studio":
            print("[+] Используется LM Studio Vision...")
            return self._call_lm_studio_vision(image_path, system_instruction)
        else:
            print(f"[-] Неизвестный провайдер '{provider}' для vision_analysis. Используется LM Studio.")
            return self._call_lm_studio_vision(image_path, system_instruction)

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    print("API key loaded:", bool(api_key))
    print("API key prefix:", api_key[:10] + "..." if api_key else "NOT FOUND")
