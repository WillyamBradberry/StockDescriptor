import os
import winreg
import shutil

def find_lm_studio_path():
    # 1. Пробуем через CLI lms в PATH
    lms_bin = shutil.which("lms")
    if lms_bin:
        parent_dir = os.path.dirname(os.path.dirname(lms_bin))
        possible_exe = os.path.join(parent_dir, "LM Studio.exe")
        if os.path.exists(possible_exe):
            return possible_exe

    # 2. Ищем в реестре Windows
    registry_keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    for hive, subkey in registry_keys:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as sub:
                            try:
                                display_name = winreg.QueryValueEx(sub, "DisplayName")[0]
                                if "LM Studio" in display_name:
                                    install_loc = winreg.QueryValueEx(sub, "InstallLocation")[0]
                                    exe_path = os.path.join(install_loc, "LM Studio.exe")
                                    if os.path.exists(exe_path):
                                        return exe_path
                            except OSError:
                                continue
                    except OSError:
                        continue
        except OSError:
            pass

    # 3. Стандартные папки в AppData
    local_app_data = os.getenv("LOCALAPPDATA", "")
    hardcoded_paths = [
        os.path.join(local_app_data, "Programs", "LM-Studio", "LM Studio.exe"),
        os.path.join(local_app_data, "LM-Studio", "LM Studio.exe"),
    ]
    for path in hardcoded_paths:
        if os.path.exists(path):
            return path

    return None

path = find_lm_studio_path()
if path:
    print(f"[+] Путь к LM Studio найден: {path}")
else:
    print("[-] LM Studio не найден.")