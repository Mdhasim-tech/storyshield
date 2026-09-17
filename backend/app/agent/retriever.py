def get_safe_chunks(collection, chapter_order, page, question, k=5):
    """
    Only returns chunks whose position is at or before the reader's
    current position. Distances are returned too, so callers can
    detect "technically allowed but not actually relevant" cases.
    """
    results = collection.query(
        query_texts=[question],
        n_results=k,
        where={
            "$or": [
                {"chapter_order": {"$lt": chapter_order}},
                {
                    "$and": [
                        {"chapter_order": chapter_order},
                        {"page_start": {"$lte": page}}
                    ]
                }
            ]
        }
    )
    return results