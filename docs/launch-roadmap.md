# StoryShield Launch Roadmap

## Done

- User auth flow with login/register
- JWT-protected API routes
- PDF upload endpoint
- PDF serving route
- PDF text extraction
- Chapter detection and grouping
- Chunking and vector indexing
- Book progress storage and retrieval
- Reader UI shell with upload flow
- Chatbot Q&A flow wired to backend
- Basic spoiler-safe guardrails

## Still left before launch

### 1. Improve reading-position accuracy
- Auto-detect chapter/page from the PDF viewer more reliably
- Tie page/chapter navigation to actual book metadata
- Add better state syncing when switching books

### 2. Improve retrieval quality
- Tune embedding and chunk size settings
- Add better relevance filtering for summary questions
- Reduce false “not enough context” blocks

### 3. Strengthen assistant behavior
- Add explicit summary vs spoiler rules
- Add answer confidence checks
- Handle vague or broad book questions more naturally

### 4. Harden backend reliability
- Add validation for malformed uploads
- Handle missing/invalid Mongo/Chroma connections gracefully
- Add retry logic and better logging

### 5. Improve UX
- Show loading states during upload and indexing
- Present chapter/page in a cleaner reader UI
- Add better error messages for upload and retrieval failures

### 6. Deployment prep
- Set up environment config for production
- Add a proper deployment script or Docker setup
- Configure production Mongo and Chroma services

### 7. Test coverage
- Add backend tests for auth, upload, retrieval, and answer logic
- Add frontend tests for login and book flow
- Run regression checks before each release

## Suggested next milestone

The app is already a strong MVP for a local demo. For launch readiness, the next big wins are:

1. Auto chapter/page tracking
2. Better summary/spoiler logic
3. Better retrieval quality
4. Production deployment config
5. Solid regression tests
