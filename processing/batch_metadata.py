import os
import base64
import requests
import time
import sys
import subprocess
import argparse
from pathlib import Path


# ================= НАСТРОЙКИ ПО УМОЛЧАНИЮ =================
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen3.6-35b-a3b"

BATCH_SIZE = 3                    # 2-3 рекомендуется
DELAY_BETWEEN_BATCHES = 3         # секунды
# ==========================================================


def image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


def generate_metadata_for_folder(image_folder: Path, thumbs_folder: Path, mock: bool = False):
    METADATA_FILE = image_folder / "METADATA.md"

    print("=== Запуск генерации метаданных ===\n")
    print(f"Исходная папка: {image_folder}")
    print(f"Папка с thumbnails: {thumbs_folder}\n")

    if not thumbs_folder.exists():
        print(f"Ошибка: THMBS папка не найдена: {thumbs_folder}")
        return None

    images = sorted(list(thumbs_folder.glob("*.jpg")))
    print(f"Найдено изображений: {len(images)}\n")

    all_results = []

    for i in range(0, len(images), BATCH_SIZE):
        batch = images[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"Обработка батча {batch_num}/{(len(images)+BATCH_SIZE-1)//BATCH_SIZE} — {len(batch)} фото")

        batch_data = []
        for img_path in batch:
            try:
                b64 = image_to_base64(img_path)
                batch_data.append((img_path, b64))
            except Exception as e:
                print(f"  Ошибка чтения {img_path.name}: {e}")

        if not batch_data:
            continue

        if mock:
            # Generate simple placeholder metadata for testing
            for img_path, _ in batch_data:
                name = img_path.name
                md = f"## {name}\n\n![[{name}|600]]\n\n**Title:**\n```\nMock title for {name}\n```\n\n**Description:**\n```\nMock description for {name}\n```\n\n**Keywords:**\n```\nmock, test\n```\n[[## Навигация]]\n---\n"
                all_results.append(md)
            print(f"  ✓ Батч {batch_num} сгенерирован (mock)")
        else:
            messages = [
                {
                    "role": "system",
                    "content": """You are a professional stock photo metadata expert for photobanks.

**Your Task:**  \nAnalyze all images (photos) create high-quality stock photo SEO metadata for each file.

1. **Context Analysis**
   - First, read the `README.md` file if it exists in the folder. It contains critical information about the subject (e.g., specific animal species, scientific name, location, rarity, etc.). All descriptions must take this information into account.
   - If no README.md exists, work only with what you see in the images.

2. **For each image create:**
   - **Title** — 60-80 characters maximum (including spaces). Make it attractive, specific, and SEO-friendly.
   - **Description** — 120-180 characters. Detailed, engaging, and professional — suitable for stock photo platforms.
   - **Keywords** — 30-40 keywords/phrases, comma-separated. Include both general and highly specific terms (scientific names, behavior, lighting, location, composition, etc.).

Output strictly in this format for each image as shown in examples in the README. Be detailed, commercial and accurate."""
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
                response = requests.post(
                    LM_STUDIO_URL,
                    json={
                        "model": MODEL,
                        "messages": messages,
                        "temperature": 0.65,
                        "max_tokens": 4000
                    },
                    timeout=300
                )

                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"]
                    all_results.append(result)
                    print(f"  ✓ Батч {batch_num} успешно обработан")
                else:
                    print(f"  ✗ Ошибка API: {response.status_code}")

            except Exception as e:
                print(f"  ✗ Ошибка запроса: {e}")

        time.sleep(DELAY_BETWEEN_BATCHES)

    # Save results
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_results))

    print(f"\n🎉 ГОТОВО!")
    print(f"Файл сохранён: {METADATA_FILE}")
    print(f"Обработано фото: {len(images)}")

    return METADATA_FILE


def generate_preview_file(image_folder: Path, metadata_file: Path, thumbs_folder: Path):
    import re

    preview_file = image_folder / 'METADATA_PREVIEW.md'
    text = metadata_file.read_text(encoding='utf-8')

    # Find blocks starting with ## filename.jpg
    pattern = re.compile(r'##\s*(.+?\.jpg)\s*(.*?)(?=\n##\s*.+?\.jpg|\Z)', re.S | re.I)
    matches = pattern.findall(text)

    if not matches:
        print('No metadata blocks found to build preview.')
        return preview_file

    lines = ["# Metadata Preview\n"]

    for filename, block in matches:
        thumb_rel = f"THMBS/{filename}"
        # extract Title, Description, Keywords
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
    # Run PowerShell script to inject metadata
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


def main():
    parser = argparse.ArgumentParser(description='Batch generate metadata and optionally inject EXIF')
    parser.add_argument('image_folder', nargs='?', default='.', help='Path to folder with original images')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Batch size')
    parser.add_argument('--delay', type=int, default=DELAY_BETWEEN_BATCHES, help='Delay between batches (s)')
    parser.add_argument('--no-inject', action='store_true', help='Do not run write_exif.ps1 after generation')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode (no API calls)')
    args = parser.parse_args()

    image_folder = Path(args.image_folder).resolve()
    thumbs_folder = image_folder / 'THMBS'

    global BATCH_SIZE, DELAY_BETWEEN_BATCHES
    BATCH_SIZE = args.batch_size
    DELAY_BETWEEN_BATCHES = args.delay

    metadata_file = generate_metadata_for_folder(image_folder, thumbs_folder, mock=args.mock)
    if not metadata_file:
        print('Metadata generation failed or no thumbnails found.')
        return
    # generate preview file for quick review
    try:
        generate_preview_file(image_folder, Path(metadata_file), thumbs_folder)
    except Exception as e:
        print(f'Failed to generate preview: {e}')

    if args.no_inject:
        print('Skipping EXIF injection as requested.')
        return

    # Locate write_exif.ps1: check image folder first, then script directory
    script_dir = Path(__file__).parent
    candidate = image_folder / 'write_exif.ps1'
    if not candidate.exists():
        candidate = script_dir / 'write_exif.ps1'

    if not candidate.exists():
        print('write_exif.ps1 not found; skipping injection.')
        return

    success = run_write_exif(image_folder, candidate)
    if success:
        print('EXIF injection completed successfully.')
    else:
        print('EXIF injection failed. Check write_exif.ps1 and ExifTool path.')


if __name__ == '__main__':
    main()