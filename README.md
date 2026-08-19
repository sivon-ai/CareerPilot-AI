# CareerPilot-AI

CareerPilot-AI is a simple AI-powered career assistant application with:

- FastAPI backend
- PDF document upload and search support
- Chat endpoint powered by OpenAI when configured
- Lightweight frontend for demo usage

## Structure

```text
careerpilot-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py
│   │   │   └── documents.py
│   │   ├── services/
│   │   │   ├── agent.py
│   │   │   └── rag.py
│   │   └── tools/
│   │       └── career_tools.py
│   ├── data/
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── .gitignore
└── README.md
```

## Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Add your OpenAI key to `backend/.env`:

```env
OPENAI_API_KEY=your_key_here
```

Start the API:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend usage

Open the frontend in a browser:

```text
frontend/index.html
```

Or serve it with a simple local web server:

```powershell
cd frontend
python -m http.server 3000
```

Then open: `http://localhost:3000`

## API endpoints

- `GET /health`
- `POST /api/chat`
- `POST /api/documents/upload`
- `GET /api/documents/search?query=...`

## Notes

- PDF upload/search uses FAISS + LangChain when OpenAI embeddings are configured.
- If no OpenAI API key is set, the chat endpoint will return a helpful configuration message instead of failing.
