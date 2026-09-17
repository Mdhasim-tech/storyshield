from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def chunk_chapters(chapters, chunk_size=1000, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True
    )

    chunks = []
    global_chunk_index = 0

    ordered_chapters = sorted(chapters.items(), key=lambda item: item[1]["chapter_order"])

    for chapter, chapter_data in ordered_chapters:
        chapter_order = chapter_data["chapter_order"]
        pages = chapter_data["pages"]

        chapter_text = ""
        page_ranges = []
        current_position = 0

        for page in pages:
            text = page["text"]
            start = current_position
            end = start + len(text)

            page_ranges.append({"start": start, "end": end, "page_number": page["page_number"]})

            chapter_text += text + "\n"
            current_position = end + 1

        document = Document(
            page_content=chapter_text,
            metadata={"chapter": chapter, "chapter_order": chapter_order}
        )

        chapter_chunks = splitter.split_documents([document])

        for i, chunk in enumerate(chapter_chunks):
            start_index = chunk.metadata["start_index"]
            end_index = start_index + len(chunk.page_content)

            pages_in_chunk = [
                p["page_number"] for p in page_ranges
                if start_index < p["end"] and end_index > p["start"]
            ]

            if not pages_in_chunk:
                continue

            chunks.append({
                "text": chunk.page_content,
                "metadata": {
                    "chapter": chapter,
                    "chapter_order": chapter_order,
                    "chunk_index": i,
                    "global_chunk_index": global_chunk_index,
                    "page_start": min(pages_in_chunk),
                    "page_end": max(pages_in_chunk)
                }
            })

            global_chunk_index += 1

    return chunks