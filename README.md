# Student Data Pipeline & UI

A full-stack application for uploading raw student records, cleaning them with explainable rules, and producing a live, eligibility-based shortlist.

The project keeps data logic in a FastAPI backend and presents results through a responsive Next.js interface. Cleaning is performed once at upload; searching, sorting, paging, shortlisting, and status filtering update instantly in the browser.

## Features

- Upload a raw CSV and view a cleaned student roster.
- Review a cleaning report with accepted, rejected, corrected, and duplicate-row counts.
- Search students by name, sort every column, and page through large datasets.
- Set a minimum Total score and view live shortlist statistics.
- Toggle students between **Active** and **Debarred**; Debarred students are immediately excluded from the shortlist.
- Export the current shortlist as a CSV.

## Architecture

```text
CSV upload → FastAPI cleaning API → cleaned roster + audit report
                                      ↓
                              Next.js user interface
                           search / sort / paging / shortlist
```

| Layer | Technology | Responsibility |
|---|---|---|
| Backend | FastAPI, pandas, rapidfuzz | CSV validation, data cleaning, duplicate checks, status API |
| Frontend | Next.js, TypeScript, Tailwind CSS | Upload workflow, table UI, live filters, export |

## Data-cleaning approach

The pipeline is designed to be deterministic and auditable. It avoids silently inventing data or automatically merging ambiguous records.

| Input issue | Rule applied | Result |
|---|---|---|
| Stray name formatting | Trim whitespace and surrounding quotes; title-case the name | `Navya'` → `Navya` |
| Gender variants | Standardise `M`/`male` and `F`/`female` | Other values become `Unknown` and are reported |
| Grade labels | Extract the numeric grade | `Grade 11` → `11` |
| Scores with labels | Parse embedded numeric values | `28 marks` → `28` |
| Missing, nonnumeric, or out-of-range scores | Reject the row and record its CSV row number and reason | No score is guessed or imputed |
| Uploaded Total | Recalculate `Math + Science + English` | Uploaded Total is never trusted |
| Exact duplicates | Remove only identical normalised records | Count appears in the cleaning report |
| Similar names | Flag possible matches using fuzzy matching | Never merged automatically; requires human review |

Every upload returns a visible report with the applicable rules, rejected-row reasons, Total corrections, and possible duplicate-review flags.

## Run locally

### Prerequisites

- Python 3.11 or later
- Node.js 18 or later

The backend is pinned to Python 3.12 for repeatable cloud deployments (see `backend/.python-version`).

### 1. Start the backend

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

```bash
# macOS / Linux
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

Install dependencies and start FastAPI:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then run:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. Run tests

```bash
cd backend
pytest
```

The backend tests cover required-column validation, name/gender/grade normalization, invalid score rejection, exact duplicate removal, and Total recalculation.

## Deployment note

The intended deployment is FastAPI on Render and Next.js on Vercel. Configure `NEXT_PUBLIC_API_URL` in Vercel with the deployed API URL and set the backend `ALLOWED_ORIGINS` variable to the deployed Vercel URL. When deploying the backend with `backend` as the Render Root Directory, the committed `.python-version` file selects Python 3.12.

The current backend stores the uploaded roster and Active/Debarred statuses in memory. This is suitable for the assessment demonstration; a database should be added before using the app for persistent production records.

## Performance

A local benchmark was run using the same CSV upload and measured the end-to-end upload/API response time as well as each cleaning stage.

| Metric | Localhost |
|---|---:|
| Upload + API response | **1,917.20 ms** |
| CSV parsing | **96.18 ms** |
| Validation & normalization | **352.13 ms** |
| Exact deduplication | **7.33 ms** |
| Fuzzy duplicate review | **65.94 ms** |
| Total cleaning | **524.79 ms** |

The benchmark shows that the complete cleaning pipeline runs in approximately **0.52 seconds** on localhost, while the end-to-end upload and API response completes in approximately **1.92 seconds**.

Performance timings are environment-dependent and may vary between local and cloud deployments due to network latency, compute resources, and platform overhead.

## AI assistance disclosure

AI was used as a development assistant, not as an autonomous decision-maker for the data.

- It helped scaffold boilerplate FastAPI and Next.js code, draft Tailwind CSS, and suggest UI structure.
- It assisted with debugging TypeScript/build issues and generating initial test cases.

## Demo video

[![Watch the demo](.\frontend\assets\student-data.png)](https://youtu.be/7msdAaWiyL8)
