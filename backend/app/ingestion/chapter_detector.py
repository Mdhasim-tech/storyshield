import re

def detect_chapter(text):
    pattern = r"\bCHAPTER\s+([IVXLCDM]+)\b"
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return f"Chapter {match.group(1)}"

    return None

def chapterize_pages(pages):
    current_chapter = "Front Matter"
    current_chapter_order = 0

    for page in pages:
        chapter = detect_chapter(page["text"])

        if chapter:
            current_chapter = chapter
            current_chapter_order += 1

        page["chapter"] = current_chapter
        page["chapter_order"] = current_chapter_order

    return pages

def group_by_chapter(pages):
    chapters = {}

    for page in pages:
        chapter = page["chapter"]

        if chapter not in chapters:
            chapters[chapter] = {
                "chapter_order": page["chapter_order"],
                "pages": []
            }

        chapters[chapter]["pages"].append(page)

    return chapters