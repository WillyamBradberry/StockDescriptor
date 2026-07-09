import os
import base64
import requests
import time
import sys
from pathlib import Path

# ================= НАСТРОЙКИ =================
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen3.6-35b-a3b"
#MODEL = "qwen/qwen3.6-27b"


BATCH_SIZE = 3                    # 2-3 рекомендуется
DELAY_BETWEEN_BATCHES = 3         # секунды
# ============================================

def image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# Получаем путь из аргумента командной строки
if len(sys.argv) > 1:
    thumbs_path = Path(sys.argv[1])
else:
    thumbs_path = Path(r"D:\projects\AI\stock-descriptor\processing\THMBS")

if not thumbs_path.exists():
    print(f"Ошибка: Папка не найдена: {thumbs_path}")
    print("Использование: python batch_metadata.py \"путь\\к\\папке\"")
    sys.exit(1)

METADATA_FILE = thumbs_path / "METADATA.md"

print("=== Запуск генерации метаданных ===\n")
print(f"Папка с thumbnails: {thumbs_path}\n")

# Получаем все изображения
images = sorted(list(thumbs_path.glob("*.jpg")))
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

    messages = [
        {
            "role": "system",
            "content": """You are a professional stock photo metadata expert for photobanks.

**Your Task:**  
Analyze all images (photos) create high-quality stock photo SEO metadata for each file.

1. **Context Analysis**
   - First, read the `README.md` file if it exists in the folder. It contains critical information about the subject (e.g., specific animal species, scientific name, location, rarity, etc.). All descriptions must take this information into account.
   - If no README.md exists, work only with what you see in the images.

2. **For each image create:**
   - **Title** — 60-80 characters maximum (including spaces). Make it attractive, specific, and SEO-friendly.
   - **Description** — 120-180 characters. Detailed, engaging, and professional — suitable for stock photo platforms.
   - **Keywords** — 30-40 keywords/phrases, comma-separated. Include both general and highly specific terms (scientific names, behavior, lighting, location, composition, etc.).

Output strictly in this format for each image:

## filename.jpg

![[image name.jpg|600]]

**Title:** 
```
[Insert title here]
```

**Description:**  
```
[Insert description here]
```

**Keywords:**  
```
[Insert keywords here]
```
[[## Навигация]]
---

Be detailed, commercial and accurate."""
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

# Сохраняем результат
with open(METADATA_FILE, "w", encoding="utf-8") as f:
    f.write("\n\n".join(all_results))

print(f"\n🎉 ГОТОВО!")
print(f"Файл сохранён: {METADATA_FILE}")
print(f"Обработано фото: {len(images)}")