# StoryShield

StoryShield is a reading assistant app that lets a user upload a book, read it in-app, and ask spoiler-safe questions about the current reading context.

## Features

- User authentication
- PDF upload
- Book reader view
- Reading progress tracking
- PDF text extraction and chapter grouping
- Chroma vector indexing for retrieval
- LLM-based reading assistant with spoiler-safe guardrails

## Tech stack

- Backend: Flask
- Frontend: React + Vite
- Database: MongoDB
- Vector store: Chroma
- PDF parsing: PyMuPDF
- LLM: Groq

## Project structure

```text
storyshield/
├── backend/
│   ├── app/
│   ├── uploads/
│   ├── chroma_data/
│   ├── venv/
│   ├── .env
│   ├── .gitignore
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   ├── node_modules/
│   ├── package.json
│   └── vite.config.js
├── .env.example
├── .gitignore
├── README.md
└── .venv/
```

## Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd storyshield
```

### 2. Create environment files

Copy the sample environment file and fill in your values:

```bash
cp .env.example .env
```

Then update the values in the generated `.env` file.

### 3. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Frontend setup

```bash
cd ../frontend
npm install
```

## Running the app

### Backend

```bash
cd backend
source venv/bin/activate
python run.py
```

The backend runs on:

```text
http://localhost:5000
```

### Frontend

```bash
cd frontend
npm run dev
```

The frontend runs on:

```text
http://localhost:5173
```

## Notes

- `.env` and generated local data are intentionally not committed to Git.
- Uploaded PDFs and Chroma data are generated locally during app use.
- If you are using Groq, add your key to `.env` before running the chatbot.

## Git hygiene

This project includes a root `.gitignore` to exclude local secrets, generated data, and dependency folders from version control.
