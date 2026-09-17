# StoryShield Backend

This is the backend service for StoryShield, a reading assistant that allows users to upload books, read them in-browser, and ask spoiler-safe questions grounded in the content they have already read.

## What it does

- Authenticates users with JWT-based tokens
- Stores user and book metadata in MongoDB
- Uploads and serves PDFs from the backend
- Extracts text from PDFs
- Detects chapters and groups pages
- Splits chapters into retrievable chunks
- Stores book chunks in Chroma for semantic search
- Answers reader questions using the available context only

## Main app flow

1. User signs in or registers
2. User uploads a PDF
3. Backend saves the file and indexes its content
4. Frontend reads the PDF in the app
5. User asks a reading question
6. Backend retrieves only the allowed context and answers safely

## Project structure

```text
backend/
├── app/
│   ├── agent/
│   │   ├── llm_client.py
│   │   ├── react_loop.py
│   │   └── retriever.py
│   ├── ingestion/
│   │   ├── chapter_detector.py
│   │   ├── chunker.py
│   │   └── pdf_loader.py
│   ├── routes/
│   │   ├── auth.py
│   │   └── books.py
│   ├── __init__.py
│   ├── config.py
│   └── extensions.py
├── tests/
├── uploads/
├── chroma_data/
├── .env
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

## Environment variables

Use a `.env` file in the backend folder with values like:

```env
SECRET_KEY=your-secret-key
MONGO_URI=mongodb://localhost:27017
DB_NAME=storyshield
CHROMA_PATH=./chroma_data
UPLOAD_FOLDER=./uploads
GROQ_API_KEY=your-groq-api-key
```

## Run locally

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

The app listens on:

```text
http://localhost:5000
```

## Key endpoints

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Books

- `POST /api/books/upload`
- `GET /api/books`
- `GET /api/books/<book_id>/progress`
- `PUT /api/books/<book_id>/progress`
- `POST /api/books/<book_id>/ask`

### Uploaded file serving

- `GET /uploads/<filename>`

## Current status

### Done

- Auth flow and protected routes
- Upload route for PDF files
- PDF parsing
- Chapter detection and grouping
- Chunk creation and indexing
- Context retrieval for allowed reading positions
- Spoiler-safe answer logic
- Book progress tracking endpoints

### Still to improve

- Auto-detect chapter/page from the PDF reader more accurately
- Improve chunk quality and relevance ranking
- Add stronger summary-versus-spoiler rules
- Add better error handling and validation
- Add production-ready deployment setup
- Add test coverage for ingestion and retrieval logic

## Notes

- The backend is set up for local development and should not commit secrets or generated data to Git.
- Uploaded PDFs and Chroma data are runtime artifacts and should stay local.
