from app.agent.retriever import get_safe_chunks


class FakeCollection:
    def __init__(self):
        self.query_args = None

    def query(self, **kwargs):
        self.query_args = kwargs
        return {"documents": [[]]}


def test_retrieval_is_limited_to_reading_position_by_default():
    collection = FakeCollection()

    get_safe_chunks(collection, chapter_order=2, page=5, question="Who is Alice?")

    assert collection.query_args["where"]["$or"][0] == {
        "chapter_order": {"$lt": 2}
    }
    assert collection.query_args["where"]["$or"][1]["$and"][1] == {
        "page_start": {"$lte": 5}
    }


def test_future_retrieval_omits_reading_position_filter():
    collection = FakeCollection()

    get_safe_chunks(
        collection,
        chapter_order=2,
        page=5,
        question="Who is Alice?",
        allow_future=True,
    )

    assert "where" not in collection.query_args
