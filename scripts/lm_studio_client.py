import requests
import json
import subprocess
import time
import os
import shutil

print("\033[36m    [!] lm_studio_client init...\033[0m")

class LMStudioClient:
    """Централизованный клиент для LM Studio API.
    
    Обеспечивает:
    - Проверку доступности сервера
    - Получение списка загруженных моделей
    - Автовыбор подходящей модели по ключевым словам
    - Выгрузку моделей из VRAM
    - Автозапуск LM Studio если сервер не запущен
    """

    def __init__(self, base_url="http://localhost:1234", launch_path=None):
        self.base_url = base_url.rstrip("/")
        self._api_url = self._normalize_api_url(base_url)
        self.launch_path = launch_path

    @staticmethod
    def _normalize_api_url(base_url: str) -> str:
        """Приводит URL к формату, заканчивающемуся на /v1 (OpenAI-compatible).

        LM Studio использует стандартный OpenAI API: /v1/models, /v1/chat/completions.
        """
        base_url = base_url.rstrip("/")
        # Удаляем /chat/completions если передан полный URL
        if base_url.endswith("/chat/completions"):
            base_url = base_url.replace("/chat/completions", "")
        # Если уже заканчивается на /v1 — оставляем как есть
        if base_url.endswith("/v1"):
            return base_url
        # Иначе добавляем /v1
        return f"{base_url}/v1"

    # ── Health / Models ──────────────────────────────────────────

    def is_available(self, timeout: int = 5) -> bool:
        """Проверяет, доступен ли LM Studio."""
        try:
            resp = requests.get(f"{self._api_url}/models", timeout=timeout)
            return resp.status_code == 200
        except requests.ConnectionError:
            return False

    def get_available_models(self, timeout: int = 5) -> list[str]:
        """Возвращает список ID загруженных моделей (OpenAI-compatible /v1/models)."""
        try:
            resp = requests.get(f"{self._api_url}/models", timeout=timeout)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return [m.get("id", "?") for m in data.get("data", [])]
        except Exception:
            return []

    def select_model(self, preferred_keywords: list[str] | None = None,
                     timeout: int = 5) -> str | None:
        """Возвращает ID подходящей модели или None.

        preferred_keywords — список подстрок для поиска (в порядке приоритета).
        Если ни одна не найдена, возвращает первую доступную.
        """
        if preferred_keywords is None:
            preferred_keywords = [
                "qwen3.6-35b-a3b", "qwen2.5-vl", "qwen-vl",
                "qwen3", "qwen2.5", "qwen", "internvl", "llava",
            ]
        available = self.get_available_models(timeout)
        if not available:
            return None

        for keyword in preferred_keywords:
            for model_id in available:
                if keyword.lower() in model_id.lower():
                    return model_id
        # Fallback — первая модель
        return available[0]

    # ── List loaded models (lms ps) ───────────────────────────────

    def get_loaded_models_cli(self, timeout: int = 10) -> list[str]:
        """Возвращает список моделей, загруженных в VRAM, через lms ps."""
        try:
            result = subprocess.run(
                ["lms", "ps"],
                capture_output=True, text=True, timeout=timeout,
                encoding='utf-8', errors='replace'
            )
            if result.returncode != 0:
                print(f"[-] [LM Studio] lms ps failed: code={result.returncode}")
                return []

            lines = result.stdout.strip().splitlines()
            print(f"[~] [LM Studio] lms ps output:\n{result.stdout.strip()}")
            loaded = []
            for line in lines:
                if line.startswith("NAME") or line.startswith("---"):
                    continue
                parts = line.split()
                if parts:
                    loaded.append(parts[0])
            print(f"[~] [LM Studio] Parsed loaded models: {loaded}")
            return loaded
        except FileNotFoundError:
            print("[-] [LM Studio] lms не найден в PATH.")
            return []
        except subprocess.TimeoutExpired:
            print(f"[-] [LM Studio] Таймаут при lms ps ({timeout} сек).")
            return []
        except Exception as e:
            print(f"[-] [LM Studio] Ошибка lms ps: {e}")
            return []

    # ── Load model ───────────────────────────────────────────────

    def load_model(self, model_name: str, timeout: int = 120) -> bool:
        """Загружает модель через CLI: lms load <model_name>."""
        if not model_name:
            return False
        try:
            print(f"[~] [LM Studio] Загружаю модель '{model_name}' через lms load...")
            result = subprocess.run(
                ["lms", "load", model_name],
                capture_output=True, text=True, timeout=timeout,
                encoding='utf-8', errors='replace'
            )
            if result.returncode == 0:
                print(f"[+] [LM Studio] Модель '{model_name}' загружена.")
                return True
            else:
                print(f"[-] [LM Studio] Ошибка загрузки '{model_name}': code={result.returncode}, stderr={result.stderr.strip()}")
                return False
        except FileNotFoundError:
            print("[-] [LM Studio] lms не найден в PATH.")
            return False
        except subprocess.TimeoutExpired:
            print(f"[-] [LM Studio] Таймаут при загрузке '{model_name}' ({timeout} сек).")
            return False
        except Exception as e:
            print(f"[-] [LM Studio] Исключение при загрузке '{model_name}': {e}")
            return False

    def ensure_model_loaded(self, model_name: str, timeout: int = 120) -> bool:
        """Проверяет через lms ps, загружена ли модель. Если нет — загружает."""
        if not model_name:
            return False

        loaded = self.get_loaded_models_cli(timeout=5)
        for model in loaded:
            if model_name.lower() in model.lower() or model.lower() in model_name.lower():
                print(f"[~] [LM Studio] Модель '{model_name}' уже загружена (lms ps).")
                return True

        print(f"[~] [LM Studio] Модель '{model_name}' не загружена. Загружаю через lms load...")
        return self.load_model(model_name, timeout=timeout)

    # ── Unload ───────────────────────────────────────────────────

    def get_loaded_instances(self, timeout: int = 5) -> list[dict]:
        """Возвращает список загруженных инстансов (из расширенного API LM Studio).

        Каждый элемент содержит как минимум поле 'id'.
        """
        try:
            resp = requests.get(f"{self._api_url}/models", timeout=timeout)
            if resp.status_code != 200:
                return []
            models_data = resp.json()
        except Exception:
            return []

        instances: list[dict] = []
        models_list = models_data.get("models") or models_data.get("data") or []

        for model in models_list:
            model_key = model.get("key") or model.get("id") or model.get("instance_id") or "unknown"
            loaded = model.get("loaded_instances") or []
            if loaded:
                for inst in loaded:
                    inst_id = inst.get("id") or inst.get("instance_id") or model_key
                    instances.append({"id": inst_id, "model_key": model_key})
            else:
                inst_id = model.get("instance_id") or model.get("id")
                if inst_id:
                    instances.append({"id": inst_id, "model_key": model_key})

        return instances

    def _request_unload(self, unload_url: str, instance_id: str, headers: dict):
        """Отправляет команду выгрузки, пробуя разные форматы payload."""
        payloads = [
            {"instance_id": instance_id},
            {"id": instance_id},
        ]
        for payload in payloads:
            try:
                resp = requests.post(unload_url, headers=headers, json=payload, timeout=10)
                if resp.status_code == 200:
                    return resp, payload
                if resp.status_code in (400, 404):
                    continue
                return resp, payload
            except Exception:
                continue

        # Fallback: URL-based endpoint
        alternative_url = f"{unload_url}/{instance_id}"
        try:
            resp = requests.post(alternative_url, headers=headers, timeout=10)
            return resp, {"url": alternative_url}
        except Exception:
            return None, None

    def unload_all_models(self, timeout: int = 10) -> dict:
        """Выгружает все загруженные модели из VRAM.

        Использует get_available_models() + unload_model() для корректной
        работы с OpenAI-совместимым API LM Studio.

        Возвращает dict с результатами:
        {
            "unloaded": [model_id, ...],
            "failed": [(model_id, error_msg), ...],
            "nothing_to_unload": bool
        }
        """
        available = self.get_available_models(timeout)
        result = {"unloaded": [], "failed": [], "nothing_to_unload": not available}

        if not available:
            return result

        for model_id in available:
            print(f"[~] Выгрузка модели '{model_id}'...")
            if self.unload_model(model_id, timeout):
                result["unloaded"].append(model_id)
            else:
                result["failed"].append((model_id, "Не удалось выгрузить"))

        if result["unloaded"]:
            print(f"[+] LM Studio: выгружено моделей: {result['unloaded']}")
        if result["failed"]:
            print(f"[-] LM Studio: ошибки выгрузки: {result['failed']}")

        return result

    # ── Unload single model by name ─────────────────────────────

    def unload_model(self, model_id: str, timeout: int = 10) -> bool:
        """Принудительно выгружает модель из VRAM по её ID.

        ВНИМАНИЕ: HTTP endpoint POST /v1/models/unload в данной версии LM Studio
        НЕ РАБОТАЕТ (возвращает 200, но ничего не делает).
        Поэтому используется CLI: lms unload <model_id>.

        Args:
            model_id: ID модели (например "qwen3.6-35b-a3b").
            timeout: Таймаут (не используется для CLI, есть свой таймаут 30 сек).

        Returns:
            True если выгрузка прошла успешно, False если ошибка.
        """
        if not model_id:
            return False

        import subprocess

        try:
            result = subprocess.run(
                ["lms", "unload", model_id],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print(f"[+] [LM Studio CLI] Модель '{model_id}' выгружена из VRAM.")
                return True
            else:
                print(f"[-] [LM Studio CLI] Ошибка выгрузки '{model_id}': "
                      f"code={result.returncode}, stderr={result.stderr.strip()}")
                return False
        except FileNotFoundError:
            print("[-] [LM Studio CLI] lms не найден. Убедитесь, что он установлен и доступен в PATH.")
            return False
        except subprocess.TimeoutExpired:
            print(f"[-] [LM Studio CLI] Таймаут при выгрузке '{model_id}' (30 сек).")
            return False
        except Exception as e:
            print(f"[-] [LM Studio CLI] Исключение при выгрузке '{model_id}': {e}")
            return False

    # ── Auto-start ───────────────────────────────────────────────

    def start_lm_studio(self, timeout: int = 60) -> bool:
        """Запускает LM Studio если путь задан и сервер недоступен.

        Args:
            timeout: Максимальное время ожидания запуска в секундах.

        Returns:
            True если сервер стал доступен, False если не удалось запустить.
        """
        if not self.launch_path:
            return False

        if self.is_available(timeout=3):
            print("[LM Studio] Сервер уже запущен.")
            return True

        path = os.path.expandvars(str(self.launch_path))
        if not os.path.isfile(path):
            print(f"[-] [LM Studio] Файл не найден: {path}")
            return False

        try:
            print(f"[LM Studio] Запускаю LM Studio: {path}")
            subprocess.Popen(
                [path],
                cwd=os.path.dirname(path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
            )

            if shutil.which("lms"):
                print("[LM Studio] Запускаю сервер через lms CLI...")
                subprocess.Popen(
                    ["lms", "server", "start"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False,
                )
            else:
                print("[LM Studio] lms CLI не найден в PATH. Пропускаю команду запуска сервера через CLI.")
        except Exception as e:
            print(f"[-] [LM Studio] Ошибка при запуске: {e}")
            return False

        # Ждём пока сервер станет доступен
        print(f"[LM Studio] Ожидаю запуск сервера (таймаут: {timeout} сек)...")
        start = time.time()
        while time.time() - start < timeout:
            if self.is_available(timeout=3):
                elapsed = int(time.time() - start)
                print(f"[LM Studio] Сервер доступен после автозапуска ({elapsed} сек).")
                # НЕ выгружаем модели здесь — ensure_model_loaded() загрузит нужную модель
                return True
            time.sleep(5)

        print(f"[-] [LM Studio] Сервер не стал доступен за {timeout} сек.")
        return False

    def ensure_available(self, timeout: int = 60) -> bool:
        """Проверяет доступность LM Studio; если недоступен — запускает.

        Args:
            timeout: Максимальное время ожидания запуска в секундах (по умолчанию 60).

        Returns:
            True если сервер доступен, False если не удалось запустить.
        """
        if self.is_available(timeout=5):
            return True

        if self.launch_path:
            print("[LM Studio] Сервер недоступен — пытаюсь автозапустить...")
            return self.start_lm_studio(timeout=timeout)

        print("[-] [LM Studio] Сервер недоступен и путь для автозапуска не задан. "
              "Укажите lm_studio_path в config.json или запустите LM Studio вручную.")
        return False