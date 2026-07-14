import subprocess
import time
from lm_studio_client import LMStudioClient


class ModelUnloader:
    """Утилита для выгрузки моделей из VRAM LM Studio.

    Инкапсулирует полный цикл: проверка доступности сервера,
    получение списка загруженных моделей, выгрузка и логирование результата.

    ВАЖНО: HTTP endpoint POST /v1/models/unload в некоторых версиях LM Studio
    возвращает 200, но НЕ выгружает модель. Поэтому используется CLI:
        lms unload --all   (выгружает все модели)
        lms unload <id>    (выгружает конкретную модель)

    Использование:
        unloader = ModelUnloader(lm_studio_client)
        result = unloader.free_vram()
    """

    def __init__(self, lm_studio_client: LMStudioClient):
        """
        Args:
            lm_studio_client: Инициализированный экземпляр LMStudioClient.
        """
        self.client = lm_studio_client

    def _unload_via_cli(self, model_id: str) -> bool:
        """Выгружает одну модель через CLI: lms unload <model_id>.

        Args:
            model_id: ID модели (например "qwen3.6-35b-a3b").

        Returns:
            True если выгрузка прошла успешно, False если ошибка.
        """
        if not model_id:
            return False

        try:
            result = subprocess.run(
                ["lms", "unload", model_id],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print(f"[+] [LM Studio CLI] Модель '{model_id}' выгружена.")
                return True
            else:
                print(f"[-] [LM Studio CLI] Ошибка выгрузки '{model_id}': "
                      f"code={result.returncode}, stderr={result.stderr.strip()}")
                return False
        except FileNotFoundError:
            print("[-] [LM Studio CLI] lms не найден. Убедитесь, что LM Studio установлен и lms доступен в PATH.")
            return False
        except subprocess.TimeoutExpired:
            print(f"[-] [LM Studio CLI] Таймаут при выгрузке '{model_id}' (30 сек).")
            return False
        except Exception as e:
            print(f"[-] [LM Studio CLI] Исключение при выгрузке '{model_id}': {e}")
            return False

    def _unload_all_via_cli(self) -> tuple[list[str], list[tuple[str, str]]]:
        """Выгружает все модели через CLI: lms unload --all.

        Returns:
            (unloaded: list[str], failed: list[(model_id, error)])
        """
        unloaded: list[str] = []
        failed: list[tuple[str, str]] = []

        try:
            result = subprocess.run(
                ["lms", "unload", "--all"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                stdout = result.stdout.strip()
                stderr_out = result.stderr.strip()

                print(f"[~] [LM Studio CLI] stdout: '{stdout}'")
                print(f"[~] [LM Studio CLI] stderr: '{stderr_out}'")

                # Объединяем stdout и stderr для анализа
                combined = stdout + " " + stderr_out

                # Проверяем, есть ли сообщение об отсутствии моделей для выгрузки
                if "No models to unload" in combined or "nothing to unload" in combined.lower():
                    print("[~] [LM Studio CLI] Нет загруженных моделей.")
                    return unloaded, failed

                # Если exit code 0 и есть упоминание "Unloaded" или просто непустой вывод — считаем успехом
                if "Unload" in combined or "Unloaded" in combined or stdout or stderr_out:
                    unloaded.append("*lms_unload_all*")
                    print("[+] [LM Studio CLI] Все модели выгружены через 'lms unload --all'.")
                else:
                    print("[~] [LM Studio CLI] Вывод пуст, но exit code=0. Считаем успехом.")
                    unloaded.append("*lms_unload_all*")

                return unloaded, failed
            else:
                print(f"[-] [LM Studio CLI] 'lms unload --all' не сработал: "
                      f"code={result.returncode}, stderr={result.stderr.strip()}")
                failed.append(("*cli_all*", f"lms exit code {result.returncode}"))
                return unloaded, failed

        except FileNotFoundError:
            print("[-] [LM Studio CLI] lms не найден в PATH.")
            failed.append(("*cli_all*", "lms CLI not found"))
            return unloaded, failed
        except subprocess.TimeoutExpired:
            print("[-] [LM Studio CLI] Таймаут при 'lms unload --all' (30 сек).")
            failed.append(("*cli_all*", "Timeout"))
            return unloaded, failed
        except Exception as e:
            print(f"[-] [LM Studio CLI] Исключение при 'lms unload --all': {e}")
            failed.append(("*cli_all*", str(e)))
            return unloaded, failed

    def free_vram(self, timeout: int = 10, verbose: bool = True) -> dict:
        """Выгружает все загруженные модели из VRAM с логированием.

        Использует 'lms unload --all' — единственный надёжный способ
        в современных версиях LM Studio (HTTP endpoint POST /v1/models/unload
        не работает — возвращает 200, но ничего не делает).

        Args:
            timeout: Таймаут для проверок (сек). Не используется для CLI,
                     т.к. у subprocess свой таймаут (30 сек).
            verbose: Если False, подавляет детальные логи о списке моделей.

        Returns:
            dict с ключами:
                "success"          — bool, True если хотя бы что-то выгружено
                "unloaded"         — list[str] ID успешно выгруженных моделей
                "failed"           — list[(str, str)] пары (instance_id, ошибка)
                "nothing_to_unload" — bool, True если VRAM уже была свободна
                "server_down"      — bool, True если LM Studio недоступен
                "method"           — str, "cli" или "fallback_http"
        """
        result: dict = {
            "success": False,
            "unloaded": [],
            "failed": [],
            "nothing_to_unload": False,
            "server_down": False,
            "method": "cli",
        }

        # 1. Проверка доступности сервера (только один запрос /v1/models вместо двух)
        if not self.client.is_available():
            if verbose:
                print("[-] LM Studio не запущен или недоступен.")
            result["server_down"] = True
            return result

        # 2. Получить список загруженных моделей (для диагностики)
        available_models = self.client.get_available_models(timeout)
        if not available_models:
            result["nothing_to_unload"] = True
            if verbose:
                print("[+] VRAM уже свободна, выгрузка не требуется.")
            return result

        if verbose:
            print(f"[~] Найдено загруженных моделей: {available_models}")

        # 3. Выгружаем через CLI (без лишних логов в консоль)
        unloaded, failed = self._unload_all_via_cli()

        result["unloaded"] = unloaded
        result["failed"] = failed

        # 4. Логирование и небольшое ожидание
        if unloaded:
            result["success"] = True
            if verbose:
                print(f"[+] Успешно выгружено моделей: {len(unloaded)}")
        elif failed and not unloaded:
            if verbose:
                print("[!] CLI не сработал. Пробую HTTP fallback...")
            result["method"] = "fallback_http"
            for model_id in available_models:
                if self._unload_via_cli(model_id):
                    result["unloaded"].append(model_id)
                else:
                    result["failed"].append((model_id, "CLI fallback не сработал"))
            if result["unloaded"]:
                result["success"] = True
        # else: nothing to unload — no log needed when !verbose

        # Небольшая пауза чтобы система освободила VRAM
        if result["success"]:
            if verbose:
                print("[~] Ожидание 2 сек после выгрузки...")
            time.sleep(2)

        return result


def unload_all() -> None:
    """Standalone compatibility wrapper for vram_manager.py and queue.py.
    
    Calls 'lms unload --all' directly via subprocess, same as ModelUnloader._unload_all_via_cli.
    """
    import subprocess
    try:
        result = subprocess.run(
            ["lms", "unload", "--all"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print("[+] [unload_all] Все модели выгружены.")
        else:
            print(f"[-] [unload_all] lms exit code {result.returncode}: {result.stderr.strip()}")
    except FileNotFoundError:
        print("[-] [unload_all] lms не найден в PATH.")
    except Exception as e:
        print(f"[-] [unload_all] Ошибка: {e}")
