# Iris Data Collection

This repo contains a **FastAPI backend** and a **vanilla HTML/JS frontend** for collecting iris images with explicit consent and self-reported health labels.


🐍 Backend Setup (with Python virtual environment)

1. Clone the repo and then run:

```bash
cd iris-collect/backend
```

2. Create and activate a virtual environment:

Try to keep the python version as 3.11 for compatibility 

```bash
# create venv folder named .venv
python -m venv .venv

# activate it
# On Linux / macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate
```

3. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```
---

## ⚡ Quick Start (UI-only Demo, No AWS)

If you only want to preview the **UI** (no database, no S3):

1. Go to the `frontend/` folder.
2. Start a simple local server:
```bash
   cd frontend
   python -m http.server 5173
```
3. Open http://localhost:5173 in your browser.
4. Select an image, tick consent, hit Submit.
- In demo mode, you’ll see a preview and a fake submission ID.
- Nothing is uploaded.