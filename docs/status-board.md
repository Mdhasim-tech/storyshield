# StoryShield Status Board

## Completed

- User authentication and JWT-protected routes
- MongoDB setup and app configuration
- PDF upload endpoint
- PDF serving route for in-app reading
- PDF text extraction
- Chapter detection and grouping
- Chunking and indexing into Chroma
- Book list and progress endpoints
- Frontend login flow
- Frontend book upload flow
- Frontend reader shell
- Basic chat assistant wiring to backend
- Spoiler-safe reading guardrails
- Local repo hygiene with `.gitignore` and `.env.example`
- Project documentation for backend, app flow, and launch roadmap

## In progress

- Better chapter/page auto-tracking from the reader
- More accurate retrieval relevance tuning
- Summary-vs-spoiler logic refinement
- Cleaner upload/indexing UX feedback

## Next up

- Improve reading position syncing and auto-save behavior
- Tune chunk size / retrieval quality
- Add stronger summary answers for early chapters
- Add backend validation and logging improvements
- Add production deployment configuration
- Expand test coverage

## Blocked / needs decisions

- Exact PDF page tracking inside embedded viewer requires better viewer integration or custom PDF navigation logic
- Production DB/Chroma hosting needs deployment environment choices
- LLM answer quality depends on the retrieval tuning and prompt refinement

## Launch readiness

### MVP ready for local demo
- Yes

### Production-ready
- Not yet

## Suggested next milestone

Focus on:
1. better reading-position tracking
2. better retrieval relevance
3. sharper summary/spoiler rules
4. deployment configuration
5. tests and regression checks
