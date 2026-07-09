**Your Task:**  
Analyze all images (photos) attached and create high-quality stock photo metadata for each file.

Read file names in processing\THMBS\images_index.md
if the file does not exist then run D:\projects\AI\stock-descriptor\processing\THMBS> . .\create_index.ps1 
first, wait for it's done then check the file images_index.md again

### Rules:

1. **Context Analysis**
   - First, read the `README.md` file if it exists in the folder. It contains critical information about the subject (e.g., specific animal species, scientific name, location, rarity, etc.). All descriptions must take this information into account.
   - If no README.md exists, work only with what you see in the images.

2. **For each image create:**
   - **Title** — 60-80 characters maximum (including spaces). Make it attractive, specific, and SEO-friendly.
   - **Description** — 120-180 characters. Detailed, engaging, and professional — suitable for stock photo platforms.
   - **Keywords** — 30-40 keywords/phrases, comma-separated. Include both general and highly specific terms (scientific names, behavior, lighting, location, composition, etc.).

3. **Output Format**
   Create a single file named `METADATA.md` in the current folder with the following structure for each image:


## filename.jpg

![[image name.jpg|400]]

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


---
Additional Requirements:

Use multimodal vision to carefully analyze each image.
For wildlife/nature: emphasize behavior, unique features, lighting, mood, and composition.
Keywords should include both English and relevant scientific terms.
Titles should be commercial and searchable.
Descriptions should be in clear, professional English.
Prioritize details that help stock buyers find the image (angle, background, time of day, rare species, etc.).

Workflow:

Read README.md (if present)
List all image files in the folder
Analyze each image one by one
Generate the complete METADATA.md file

When you done this task ask user to process next task using:  \processing\write_exif.ps1

Work professionally and with high attention to quality.