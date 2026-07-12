#!/usr/bin/env python3
"""
StockDescriptor - batch_metadata.py
AI-powered batch generation of stock photo Title / Description / Keywords
Supports: LM Studio (local OpenAI-compatible) and Google Gemini (online)
"""

import os
import base64
import requests
import time
import sys
import subprocess
import argparse
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# ================= НАСТРОЙКИ ПО УМОЛЧАНИЮ =================
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen3.6-35b-a3b"

DEFAULT_BATCH_SIZE = 3
DEFAULT_DELAY = 3
# ==========================================================


def image_to_base64(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


def extract_metadata_block(text: str, filename: str) -> Optional[str]:
    """
    Try to extract Title, Description, Keywords for a specific filename from LLM response text.
    Returns a formatted markdown block string or None if extraction failed.
    """
    sections_by_filename: Dict[str, str] = {}

    # Strategy A: split on ## filename.jpg headings
    heading_matches = list(re.finditer(r'##\s+(.+?\.jpg)\s*(.*?)(?=\n##\s+|\Z)', text, re.S | re.I))
    if heading_matches:
        for m in heading_matches:
            fname = m.group(1).strip().lower()
            block = m.group(0).strip()
            sections_by_filename[fname] = block

    # Strategy B: split on --- and try to match filenames
    if not sections_by_filename:
        dash_sections = re.split(r'\n---+\s*\n', text)
        for s in dash_sections:
            fname_m = re.search(r'(?:^|\s)(\S+\.jpg)', s[:200], re.I)
            if fname_m:
                fname = fname_m.group(1).strip().lower()
                sections_by_filename[fname] = s.strip()

    # Strategy C: split on **Title:** boundaries
    if not sections_by_filename:
        title_sections = re.split(r'\*\*Title:\*\*', text)
        if len(title_sections) > 1:
            for i, s in enumerate(title_sections):
                if i == 0:
                    continue
                fname_m = re.search(r'(?:^|\s)(\S+\.jpg)', s[:200], re.I)
                if fname_m:
                    fname = fname_m.group(1).strip().lower()
                    sections_by_filename[fname] = "**Title:**\n" + s.strip()

    # Strategy D: fallback — use whole text
    block_str = sections_by_filename.get(filename.lower(), text)

    # Extract Title, Description, Keywords
    title_m = re.search(r'\*\*Title:\*\*\s*\n*`{3,}\s*\n?(.*?)\n?`{3,}', block_str, re.S | re.I)
    desc_m = re.search(r'\*\*Description:\*\*\s*\n*`{3,}\s*\n?(.*?)\n?`{3,}', block_str, re.S | re.I)
    kw_m = re.search(r'\*\*Keywords:\*\*\s*\n*`{3,}\s*\n?(.*?)\n?`{3,}', block_str, re.S | re.I)

    title = title_m.group(1).strip() if title_m else None
    desc = desc_m.group(1).strip() if desc_m else None
    kw = kw_m.group(1).strip() if kw_m else None

    if title or desc or kw:
        result = f"## {filename}\n\n"
        result += f"![[{filename}|600]]\n\n"
        result += f"**Title:**\n```\n{title or ''}\n```\n\n"
        result += f"**Description:**\n```\n{desc or ''}\n```\n\n"
        result += f"**Keywords:**\n```\n{kw or ''}\n---"
        return result

    return None


def get_existing_blocks(metadata_file: Path) -> Dict[str, str]:
    """Parse METADATA.md and return {filename_lower: block_text} for already-processed images."""
    if not metadata_file.exists():
        return {}
    text = metadata_file.read_text(encoding='utf-8')
    pattern = re.compile(r'##\s*(.+?\.jpg)\s*(.*?)(?=\n##\s*|\Z)', re.S | re.I)
    blocks: Dict[str, str] = {}
    for m in pattern.finditer(text):
        fname = m.group(1).strip()
        block = m.group(0).strip()
        blocks[fname.lower()] = block
    return blocks


def append_block_to_file(metadata_file: Path, block: str):
    """Append a single metadata block to METADATA.md. Creates file if not exists."""
    mode = 'a' if metadata_file.exists() else 'w'
    prefix = '\n' if metadata_file.exists() and metadata_file.stat().st_size > 0 else ''
    with open(metadata_file, 'a', encoding='utf-8') as f:
        f.write(prefix + block + '\n')


def load_error_list(error_file: Path) -> set:
    """Load filenames from metadata_error.md, return set of lowercase names."""
    if not error_file.exists():
        return set()
    errors = set()
    text = error_file.read_text(encoding='utf-8')
    for line in text.splitlines():
        line = line.strip().lower()
        if line.endswith('.jpg'):
            errors.add(line)
    return errors


def remove_from_error_list(error_file: Path, filename: str):
    """Remove a filename from error file after successful retry."""
    if not error_file.exists():
        return
    lines = [l for l in error_file.read_text(encoding='utf-8').splitlines()
             if l.strip().lower() != filename.lower()]
    error_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def call_vision_api(provider: str, config: Dict[str, Any], batch_data: List[Tuple[Path, str]], system_prompt: str) -> str:
    """
    Unified LLM vision call for supported providers.
    Returns the raw text response from model or "ERROR: ..." string.
    """
    provider = provider.lower().strip()

    if provider == "gemini":
        api_key = config.get("gemini_api_key", "") or ""
        model = config.get("gemini_model", "gemini-1.5-flash-latest")
        if not api_key:
            return "ERROR: Gemini API key is not configured. Open Settings and save your key."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        parts = [{"text": system_prompt}]
        for img_path, b64 in batch_data:
            parts.append({"text": f"\n\nFilename: {img_path.name}\nProvide stock metadata for this exact image following the format rules above."})
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64
                }
            })

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.65,
                "maxOutputTokens": 8192
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=300, headers={"Content-Type": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    cand = data["candidates"][0]
                    if "content" in cand and "parts" in cand["content"]:
                        return cand["content"]["parts"][0].get("text", "")
                return "ERROR: Unexpected Gemini response structure: " + str(data)[:300]
            else:
                return f"ERROR: Gemini HTTP {resp.status_code} - {resp.text[:400]}"
        except Exception as e:
            return f"ERROR: Gemini request exception: {str(e)}"

    else:
        # LM Studio / OpenAI-compatible
        url = config.get("lmstudio_url", LM_STUDIO_URL)
        model = config.get("lmstudio_model", MODEL)

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        for img_path, b64 in batch_data:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Filename: {img_path.name}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            })

        try:
            resp = requests.post(
                url,
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.65,
                    "max_tokens": 4000
                },
                timeout=300
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                return f"ERROR: {provider} HTTP {resp.status_code} - {resp.text[:400]}"
        except Exception as e:
            return f"ERROR: {provider} request failed: {str(e)}"


def generate_metadata_for_folder(image_folder: Path,
                                 thumbs_folder: Path,
                                 batch_size: int = DEFAULT_BATCH_SIZE,
                                 delay: int = DEFAULT_DELAY,
                                 mock: bool = False,
                                 check_errs: bool = False,
                                 llm_config: Optional[Dict[str, Any]] = None) -> Tuple[Path, Optional[Path]]:
    """
    Main function. Now supports llm_config for multi-provider (lmstudio / gemini).
    """
    if llm_config is None:
        try:
            from _config_manager import load_config
            llm_config = load_config()
        except Exception:
            llm_config = {}

    provider = llm_config.get("provider", "lmstudio").lower()
    METADATA_FILE = image_folder / "METADATA.md"
    ERROR_FILE = image_folder / "metadata_error.md"

    print("=== Запуск генерации метаданных ===\n")
    print(f"Исходная папка: {image_folder}")
    print(f"Папка с thumbnails: {thumbs_folder}")
    print(f"Провайдер AI: {provider.upper()}\n")

    if not thumbs_folder.exists():
        print(f"Ошибка: THMBS папка не найдена: {thumbs_folder}")
        return METADATA_FILE, None

    all_images = sorted(list(thumbs_folder.glob("*.jpg")))
    print(f"Найдено изображений: {len(all_images)}\n")

    # Decide which images to process
    if check_errs and ERROR_FILE.exists():
        error_fnames = load_error_list(ERROR_FILE)
        images = [img for img in all_images if img.name.lower() in error_fnames]
        if not images:
            print("Нет файлов в metadata_error.md. Нечего переобрабатывать.")
            return METADATA_FILE, ERROR_FILE
        print(f"Режим --check-errs: переобработка {len(images)} ошибочных файлов")
        for img in images:
            remove_from_error_list(ERROR_FILE, img.name)
    else:
        existing_blocks = get_existing_blocks(METADATA_FILE)
        if existing_blocks:
            print(f"Resume mode: {len(existing_blocks)} уже обработано")
        images = [img for img in all_images if img.name.lower() not in existing_blocks]

    if not images:
        print("Все изображения уже обработаны. Пропускаем генерацию.")
        return METADATA_FILE, ERROR_FILE

    print(f"Изображений для обработки: {len(images)}\n")

    current_errors: set = set()

    # System prompt (shared)
    system_prompt = (
        "You are a professional stock photo metadata generator. "
        "Output ONLY the metadata blocks in the exact format requested. NO thinking, NO reasoning, NO extra text outside the blocks.\n\n"
        "**Rules:**\n"
        "1. If a README.md exists in the image folder — read it and use the context (species, location, unique facts).\n"
        "2. For EVERY image create three fields:\n"
        "   - **Title** — 60-80 characters, attractive, SEO-optimized for stock platforms.\n"
        "   - **Description** — 120-180 characters, detailed, professional, vivid but factual.\n"
        "   - **Keywords** — 30-40 comma-separated keywords (no duplicates, good for search).\n\n"
        "**STRICT OUTPUT FORMAT (one block per image, nothing else):**\n\n"
        "## image1.jpg\n\n"
        "![[image1.jpg|600]]\n\n"
        "**Title:**\n```\nAttractive Title Here\n```\n\n"
        "**Description:**\n```\nDetailed professional description here.\n```\n\n"
        "**Keywords:**\n```\nkeyword1, keyword2, keyword3, ...\n```\n---\n\n"
        "## image2.jpg\n\n..."
    )

    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(images) + batch_size - 1) // batch_size
        print(f"Обработка батча {batch_num}/{total_batches} — {len(batch)} фото")

        batch_data: List[Tuple[Path, str]] = []
        for img_path in batch:
            try:
                b64 = image_to_base64(img_path)
                batch_data.append((img_path, b64))
            except Exception as e:
                print(f"  Ошибка чтения {img_path.name}: {e}")
                current_errors.add(img_path.name.lower())

        if not batch_data:
            continue

        if mock:
            for img_path, _ in batch_data:
                name = img_path.name
                block = (
                    f"## {name}\n\n"
                    f"![[{name}|600]]\n\n"
                    f"**Title:**\n```\nMock title for {name}\n```\n\n"
                    f"**Description:**\n```\nMock description for {name}\n```\n\n"
                    f"**Keywords:**\n```\nmock, test, stock, photo\n```\n---"
                )
                append_block_to_file(METADATA_FILE, block)
            print(f"  ✓ Батч {batch_num} сгенерирован (mock)")
        else:
            result = call_vision_api(provider, llm_config, batch_data, system_prompt)

            if result.startswith("ERROR:"):
                print(f"  {result}")
                for img_path, _ in batch_data:
                    current_errors.add(img_path.name.lower())
            else:
                print(f"  Ответ модели ({len(result)} символов)")

                batch_ok = 0
                for img_path, _ in batch_data:
                    fname_lower = img_path.name.lower()
                    block = extract_metadata_block(result, img_path.name)
                    if block:
                        append_block_to_file(METADATA_FILE, block)
                        batch_ok += 1
                    else:
                        print(f"  ✗ Не удалось извлечь метаданные для {img_path.name}")
                        current_errors.add(fname_lower)

                if batch_ok:
                    print(f"  ✓ Батч {batch_num}: обработано {batch_ok}/{len(batch_data)} фото")
                else:
                    print(f"  ✗ Батч {batch_num}: ни один блок не извлечён")
                    print(f"    Первые 300 символов ответа: {result[:300]!r}")

        time.sleep(delay)

    # ---- Save errors to metadata_error.md ----
    if current_errors:
        existing_errors = load_error_list(ERROR_FILE)
        all_errors = existing_errors | current_errors
        sorted_errors = sorted(all_errors)
        with open(ERROR_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted_errors) + '\n')
        print(f"\n⚠️  Ошибки: {len(current_errors)} файлов записано в {ERROR_FILE.name}")
        for name in sorted(current_errors):
            print(f"     - {name}")
    else:
        if ERROR_FILE.exists():
            ERROR_FILE.unlink()
            print(f"\n✅ Файл ошибок удалён — все изображения обработаны успешно")

    # ---- Final sort ----
    all_blocks = get_existing_blocks(METADATA_FILE)
    if all_blocks:
        sorted_fnames = sorted(all_blocks.keys())
        combined = "\n\n".join(all_blocks[fname] for fname in sorted_fnames) + "\n"
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            f.write(combined)

    print(f"\n🎉 ГОТОВО!")
    print(f"Файл: {METADATA_FILE}")
    print(f"Обработано изображений: {len(images)}")

    return METADATA_FILE, ERROR_FILE


def generate_preview_file(image_folder: Path, metadata_file: Path, thumbs_folder: Path):
    preview_file = image_folder / 'METADATA_PREVIEW.md'
    text = metadata_file.read_text(encoding='utf-8')

    pattern = re.compile(r'##\s*(.+?\.jpg)\s*(.*?)(?=\n##\s*.+?\.jpg|\Z)', re.S | re.I)
    matches = pattern.findall(text)

    if not matches:
        print('No metadata blocks found to build preview.')
        return preview_file

    lines = ["# Metadata Preview\n"]

    for filename, block in matches:
        thumb_rel = f"THMBS/{filename}"
        title_m = re.search(r"\*\*Title:\*\*\s*```\s*(.*?)\s*```", block, re.S)
        desc_m = re.search(r"\*\*Description:\*\*\s*```\s*(.*?)\s*```", block, re.S)
        kw_m = re.search(r"\*\*Keywords:\*\*\s*```\s*(.*?)\s*```", block, re.S)

        title = title_m.group(1).strip() if title_m else ''
        desc = desc_m.group(1).strip() if desc_m else ''
        kws = kw_m.group(1).strip() if kw_m else ''

        lines.append(f"## {filename}\n")
        lines.append(f"![]({thumb_rel})\n")
        if title:
            lines.append(f"**Title:** {title}\n")
        if desc:
            lines.append(f"**Description:** {desc}\n")
        if kws:
            lines.append(f"**Keywords:** {kws}\n")
        lines.append('\n---\n')

    preview_file.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Preview file generated: {preview_file}')
    return preview_file


def run_write_exif(image_folder: Path, script_path: Path):
    print(f"Запуск {script_path} для папки {image_folder}")
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-OriginalFolder",
        str(image_folder)
    ]
    try:
        res = subprocess.run(cmd, check=False)
        return res.returncode == 0
    except Exception as e:
        print(f"Ошибка запуска write_exif: {e}")
        return False


def run_nav_script(image_folder: Path, metadata_file: Path, script_dir: Path, ask: bool = False):
    candidate = script_dir / "create-metadata-nav-modified.ps1"
    if not candidate.exists():
        candidate = image_folder / "create-metadata-nav-modified.ps1"
    if not candidate.exists():
        print("create-metadata-nav-modified.ps1 not found; skipping navigation file generation.")
        return False

    if ask:
        try:
            response = input("Generate Obsidian navigation file (METADATA-NAV.md)? (Y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            response = "y"
        if response not in ("", "y", "yes"):
            print("Skipping navigation file generation.")
            return False

    print(f"Running {candidate}...")
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", str(candidate),
        "-MetadataFile", str(metadata_file)
    ]
    try:
        res = subprocess.run(cmd, check=False)
        if res.returncode == 0:
            print("Navigation file generated successfully.")
        else:
            print("Navigation file generation failed.")
        return res.returncode == 0
    except Exception as e:
        print(f"Error running navigation script: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Batch generate metadata and optionally inject EXIF (supports LM Studio & Gemini)')
    parser.add_argument('image_folder', nargs='?', default='.', help='Path to folder with original images')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size')
    parser.add_argument('--delay', type=int, default=DEFAULT_DELAY, help='Delay between batches (s)')
    parser.add_argument('--no-inject', action='store_true', help='Do not run write_exif.ps1 after generation')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode (no API calls)')
    parser.add_argument('--no-nav', action='store_true', help='Skip Obsidian navigation file generation')
    parser.add_argument('--ask-nav', action='store_true', help='Prompt before generating Obsidian navigation file')
    parser.add_argument('--check-errs', action='store_true', help='Re-analyze only files from metadata_error.md')
    parser.add_argument('--provider', choices=['lmstudio', 'gemini'], default=None, help='AI provider override')
    parser.add_argument('--model', default=None, help='Model name override')
    parser.add_argument('--api-key', default=None, help='API key for Gemini (or other online providers)')

    args = parser.parse_args()

    # Build llm_config
    try:
        from _config_manager import load_config
        llm_config = load_config()
    except Exception:
        llm_config = {}

    if args.provider:
        llm_config["provider"] = args.provider
    if args.model:
        if llm_config.get("provider") == "gemini":
            llm_config["gemini_model"] = args.model
        else:
            llm_config["lmstudio_model"] = args.model
    if args.api_key:
        llm_config["gemini_api_key"] = args.api_key   # only relevant for gemini

    image_folder = Path(args.image_folder).resolve()
    thumbs_folder = image_folder / 'THMBS'

    metadata_file, error_file = generate_metadata_for_folder(
        image_folder, thumbs_folder,
        batch_size=args.batch_size,
        delay=args.delay,
        mock=args.mock,
        check_errs=args.check_errs,
        llm_config=llm_config
    )
    if not metadata_file:
        print('Metadata generation failed or no thumbnails found.')
        return

    try:
        generate_preview_file(image_folder, Path(metadata_file), thumbs_folder)
    except Exception as e:
        print(f'Failed to generate preview: {e}')

    has_errors = error_file is not None and error_file.exists()

    if not args.no_inject:
        if has_errors:
            print("\n⚠️  Обнаружены ошибки в metadata_error.md! EXIF injection пропущен.")
            print("   Исправьте ошибки, затем запустите с флагом --check-errs.")
        else:
            script_dir = Path(__file__).parent
            candidate = image_folder / 'write_exif.ps1'
            if not candidate.exists():
                candidate = script_dir / 'write_exif.ps1'
            if not candidate.exists():
                print('write_exif.ps1 not found; skipping EXIF injection.')
            else:
                success = run_write_exif(image_folder, candidate)
                if success:
                    print('EXIF injection completed successfully.')
                else:
                    print('EXIF injection failed. Check write_exif.ps1 and ExifTool path.')
    else:
        print('Skipping EXIF injection as requested.')

    if not args.no_nav:
        script_dir = Path(__file__).parent
        run_nav_script(image_folder, metadata_file, script_dir, ask=args.ask_nav)
    else:
        print('Skipping navigation file generation as requested.')


if __name__ == '__main__':
    main()
