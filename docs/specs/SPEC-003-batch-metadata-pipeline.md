# SPEC-003: Batch Metadata Pipeline

**Status:** ✅ Done  
**Priority:** P0  
**Key File:** `processing/batch_metadata.py`  
**Dependencies:** SPEC-002 (Config), SPEC-006 (Resize)

---

## 1. Purpose

AI-powered batch generation of stock photo metadata (Title, Description, Keywords) for all JPGs in a folder. Supports LM Studio and Google Gemini. Handles resume, error recovery, and incremental writing to METADATA.md.

---

## 2. Input / Output

### 2.1 Input

| Parameter | Source | Description |
|-----------|--------|-------------|
| `image_folder` | CLI arg or GUI | Folder with original JPGs |
| `thumbs_folder` | `image_folder/THMBS` | Resized images for Vision API |
| `batch_size` | Config / CLI | Images per API call (default 3) |
| `delay` | Config / CLI | Seconds between batches (default 3) |
| `llm_config` | Config / CLI | Provider, model, API key, etc. |

### 2.2 Output

| File | Path | Content |
|------|------|---------|
| `METADATA.md` | `image_folder/METADATA.md` | Formatted blocks with Title/Description/Keywords per image |
| `METADATA_PREVIEW.md` | `image_folder/METADATA_PREVIEW.md` | Lightweight preview with thumbnails |
| `metadata_error.md` | `image_folder/metadata_error.md` | List of failed filenames (only if errors) |

### 2.3 Metadata Block Format

```markdown
## filename.jpg

![[filename.jpg|600]]

**Title:**
```
SEO-optimized title (60-80 chars)
```

**Description:**
```
Professional description (120-180 chars)
```

**Keywords:**
```
keyword1, keyword2, ..., keyword40
```
---
```

---

## 3. Core Algorithm

### 3.1 Resume Mode

1. Parse existing `METADATA.md` → extract processed filenames
2. Skip already-processed images
3. Process only remaining images

### 3.2 Error Recovery (`--check-errs`)

1. Read `metadata_error.md` → list of failed filenames
2. Re-process only failed images
3. Remove each filename from error list on success
4. Delete `metadata_error.md` if all errors resolved

### 3.3 Batch Processing

```
for each batch of N images:
  1. Read images → base64 encode
  2. Build API request with system prompt + batch images
  3. Call LLM (LM Studio or Gemini)
  4. Parse response → extract metadata blocks per filename
  5. Append valid blocks to METADATA.md
  6. Record errors for failed extractions
  7. Sleep `delay` seconds
→ Final sort: reorder all blocks alphabetically by filename
```

### 3.4 Response Parsing

Multi-strategy extraction for robustness:

| Strategy | Method |
|----------|--------|
| A | Split by `## filename.jpg` headings |
| B | Split by `---` dividers |
| C | Find filename position → extract surrounding block |
| D | Use entire response (fallback) |

Field extraction patterns (in order of priority):
1. `**Field:**``` ... ````
2. `**Field:** ```...````
3. `**Field:** ...` (up to next `**` or `---`)
4. `**Field:** ...` (up to next `##` or end)

---

## 4. System Prompt

The prompt instructs the model to:
- Act as a professional stock photo metadata generator
- Output ONLY metadata blocks (no reasoning, no extra text)
- Consider context from `README.md` if present in folder
- Generate SEO-optimized Title (60-80 chars), Description (120-180 chars), Keywords (30-40 comma-separated)

---

## 5. Provider-Specific API Calls

### 5.1 LM Studio (OpenAI-compatible)

```
POST {url}
Headers: Content-Type: application/json
Body: {
  "model": "{lmstudio_model}",
  "messages": [
    {"role": "system", "content": "{system_prompt}"},
    {"role": "user", "content": [
      {"type": "text", "text": "Filename: image1.jpg"},
      {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{b64}"}}
    ]}
  ],
  "temperature": 0.65,
  "max_tokens": 4000
}
```

### 5.2 Google Gemini

```
POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}
Body: {
  "contents": [{"parts": [
    {"text": "{system_prompt}"},
    {"text": "Filename: image1.jpg"},
    {"inline_data": {"mime_type": "image/jpeg", "data": "{b64}"}}
  ]}],
  "generationConfig": {"temperature": 0.65, "maxOutputTokens": 8192}
}
```

---

## 6. Error Handling

- **API error** (HTTP/network) → all images in batch marked as errors
- **Parse failure** (can't extract block for filename) → individual image marked as error
- **Read error** (can't open image) → individual image marked as error
- **Error file management**:
  - Errors appended to `metadata_error.md`
  - File deleted when no errors remain
  - Resume/check-errs only re-processes error files

---

## 7. CLI Interface

```
python processing/batch_metadata.py [folder] [options]

Options:
  --batch-size N     Images per API call (default 3)
  --delay N          Seconds between batches (default 3)
  --mock             Mock mode (no API calls)
  --provider         lmstudio | gemini
  --model            Model name override
  --api-key          Gemini API key
  --check-errs       Re-process only failed files
  --no-inject        Skip EXIF injection
  --no-nav           Skip Obsidian nav generation
  --ask-nav          Prompt before nav generation
```

---

*Last updated: 2026-07-14*