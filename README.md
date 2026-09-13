# ILovePDF Personal Local Replacement

A self-hosted, personal, local replacement for ILovePDF Premium built with Next.js 15, TypeScript, Python 3.12, FastAPI, pikepdf / PyPDF, LibreOffice headless, Tesseract OCR, and PostgreSQL.

> ⚠️ **NOTICE: FOR PERSONAL / LOW-STAKES USE ONLY**  
> This application is strictly designed for local, personal, and internal document processing. It deliberately omits:
> - Regulated Qualified Electronic Signatures (eIDAS / eSIGN compliant QES).
> - Government identity verification / eID integration.
> - Full Adobe Acrobat-level vector editing or enterprise document governance control planes.

---

## Key Features

- **Immutable Original Preservation**: Uploaded files are saved immutably with SHA-256 integrity verification. Originals are never modified or overwritten.
- **Versioned Outputs**: Every tool operation generates a versioned output document linked to its parent input document(s).
- **Comprehensive PDF Toolset**:
  - **Merge**: Combine multiple PDFs into a single document.
  - **Split**: Extract page ranges or split into parts.
  - **Reorder & Rotate**: Rearrange page sequence and apply 90°/180°/270° rotations.
  - **Compress**: Optimize stream objects and strip unneeded metadata.
  - **Watermark**: Overlay custom text or brand stamps with opacity and position controls.
  - **Redact**: Blackout sensitive keywords or page coordinates.
  - **OCR**: Process scanned PDFs with Tesseract OCR to create searchable text layers.
  - **Office to PDF**: Convert DOCX, XLSX, PPTX using headless LibreOffice.
  - **PDF Inspector**: Scan PDFs for custom embedded fonts, interactive form fields, existing digital signatures, and password encryption with visual warnings.
- **Simple Electronic Signatures (Self-Hosted Simple e-Sign)**:
  - Place signature, date, and text fields on PDF pages.
  - Generate secure access links for signers.
  - Record mandatory recipient electronic consent (timestamp, IP, user-agent).
  - Seal final PDF with SHA-256 hash overlay and append an Audit Certificate page.
- **Append-Only Audit Log**: Every event (upload, processing, viewing, signing, export, deletion) is logged with SHA-256 document hashes, timestamps, and client info.
- **User-Owned Local Data & 1-Click Export**:
  - Files stored locally in `./data/storage/`.
  - 1-Click full ZIP data export containing all original documents, versioned outputs, and JSON metadata.
  - File retention & auto-expiry policy enforcement.

---

## Open as a Desktop App (no Terminal)

This pack is a **folder you can copy** (USB, zip, AirDrop). Double-click — no commands.

### macOS
1. Unzip / copy the folder anywhere.
2. Double-click **`ILovePDF Personal.app`** (also in `desktop/macos/`).
3. If macOS blocks it: **right-click → Open → Open**.
4. First launch installs packages (1–3 min). After that it opens a native window.

### Windows
1. Unzip / copy the folder anywhere.
2. Double-click **`Launch ILovePDF.vbs`** (silent) or **`Launch ILovePDF.bat`**.
3. First launch installs packages, then a window / browser opens.

Master password: **`admin123`** (change in `.env`).

Your files stay **inside this folder** (`data/storage/`, `data/ilovepdf.db`). Move the whole folder and you move the app + your documents.

### Make a clean zip to give someone else
```bash
./desktop/make_pack.sh
```
Output: `dist/ILovePDF-Personal-Local-YYYYMMDD.zip` (no venv, no node_modules, no personal files).

---

## Optional: script / Docker

```bash
./start.sh
```

Or:

```bash
docker-compose up --build
```

Web GUI: `http://127.0.0.1:3000` · API: `http://127.0.0.1:8000/api/health`

---

## Environment & Configuration

Secrets are managed via `.env`. A sample configuration is shipped in `.env.example`.

```ini
DATABASE_URL=postgresql+asyncpg://pdfuser:pdfsecret@localhost:5432/ilovepdf_db
FALLBACK_SQLITE_URL=sqlite+aiosqlite:///./data/ilovepdf.db
STORAGE_DIR=./data/storage
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=dev-secret-key-change-in-production-123456789
FRONTEND_URL=http://localhost:3000
TESSERACT_CMD=tesseract
LIBREOFFICE_CMD=soffice
```

---

## Local Data Location & Backup Steps

### Data Location
All application state and files reside locally under your workspace directory:
- `./data/storage/originals/`: Immutable original uploaded files.
- `./data/storage/outputs/`: Versioned operation outputs.
- `./data/storage/backups/`: Generated export ZIP archives.
- `./data/ilovepdf.db` or PostgreSQL database: Document metadata, signature requests, and append-only audit event logs.

### Backup & Restore
1. **1-Click UI Export**: Go to **Export & Backup** in the Web GUI and click **Download Complete Export ZIP**.
2. **Manual Local Folder Copy**:
   ```bash
   cp -r ./data/storage /path/to/external/backup/
   ```

---

## Testing

Run the focused backend unit tests and end-to-end integration workflow using pytest:

```bash
PYTHONPATH=backend ./venv/bin/pytest backend/tests
```

---

## Architecture Diagram

```
+-----------------------------------------------------------------------+
|                      Next.js 15 Web Frontend                          |
|  Dashboard | Tool Workspaces | e-Sign Studio | Audit Log | Export     |
+-----------------------------------+-----------------------------------+
                                    | REST API Calls
                                    v
+-----------------------------------------------------------------------+
|                       FastAPI Python 3.12 Backend                     |
|  Services: Storage, PDF Processing, Signature Engine, Audit Logger    |
|  Tools: pikepdf/pypdf, ReportLab, Tesseract OCR, LibreOffice         |
+-------------------+-------------------------------+-------------------+
                    |                               |
                    v                               v
+-----------------------+               +-------------------------------+
|  PostgreSQL / SQLite  |               |    User-Owned File Storage    |
|  Audit & Metadata DB  |               |  ./data/storage/ (Immutable)  |
+-----------------------+               +-------------------------------+
```
