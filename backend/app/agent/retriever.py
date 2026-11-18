def get_safe_chunks(collection, chapter_order, page, question, k=5, allow_future=False):
    """
    By default, only returns chunks at or before the reader's position.
    Future chunks are included only after an explicit opt-in. Distances
    let callers detect allowed but irrelevant results.
    """
    query = {
        "query_texts": [question],
        "n_results": k,
    }

    if not allow_future:
        query["where"] = {
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

    return collection.query(**query)