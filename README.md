# smart-file-sorter

Turn a messy folder into a tidy, category-organized library. Smart File Sorter
scans a directory, classifies each file by type (Images, Documents, Audio,
Video, Code, Archives, and more), and moves everything into clean category
subfolders.

The project ships three ways to use the same core engine:

- a **Python core library** (`smart_file_sorter`) with the classification and
  move logic,
- a **CLI** (`smart-sort`) for organizing a real directory from the terminal,
- a **FastAPI + React web app** that generates a demo dataset, previews the sort
  plan, and applies it with one click.

## Layout

| Path | What it is |
| --- | --- |
| `backend/smart_file_sorter/` | Core library, CLI, and FastAPI app |
| `backend/tests/` | pytest suite for the core logic and API |
| `frontend/` | React + Vite single-page UI |
| `scripts/setup.sh` | Idempotent dependency bootstrap |
| `.cursor/environment.json` | Cloud Agent environment definition |

## Getting started

Run the one-shot bootstrap (creates a Python venv, installs backend + frontend
dependencies):

```bash
bash scripts/setup.sh
```

### Run the backend (API on port 8000)

```bash
cd backend
./.venv/bin/uvicorn smart_file_sorter.api:app --host 0.0.0.0 --port 8000
```

### Run the frontend (UI on port 5173)

```bash
cd frontend
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` calls to the
backend automatically.

### Use the CLI

```bash
# Preview (dry run)
smart-sort /path/to/messy/folder

# Actually move files into category subfolders
smart-sort /path/to/messy/folder --apply
```

## Tests

```bash
cd backend
./.venv/bin/python -m pytest
```

## How classification works

`smart_file_sorter/categories.py` holds a data-driven mapping of file extensions
to categories. Unknown or extension-less files land in `Other`. Add a new file
type by editing that single table — no logic changes required.
