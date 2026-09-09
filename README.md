# VariantDB — Genomic Variant & Sample Tracking Database

A hybrid clinical bioinformatics web application combining **Django (SQL)** for structured genomic variant curation and **MongoDB (NoSQL)** for flexible laboratory sample tracking, pipeline progression, and quality control (QC) diagnostics. Sample and variant data can be sourced either from two CSV files (`variants/data/variants.csv` and `variants/data/sample.csv`) or from live MongoDB collections, controlled by a single `DATA_SOURCE` setting (see Section 4).

---

## 1. System Overview & Architecture

* **Switchable Data Source:** A single `DATA_SOURCE` setting (`"csv"` or `"mongodb"`) determines whether sample and variant data is read from the local CSV files or from live MongoDB collections. See Section 4.
* **Genomic Variant Database (Relational SQL):** In `"csv"` mode, stores standardized, curated gene annotations and genomic variants (coordinates, alleles, allele frequency, quality scores) queried via Django ORM, seeded and kept in sync from `variants/data/variants.csv`. In `"mongodb"` mode, variants are read directly from a MongoDB `variants` collection instead.
* **Sample Tracking & QC LIMS (Document NoSQL):** Manages laboratory sequencing status, pipeline milestone progress, and detailed QC test pass/fail metrics, read from either MongoDB (via PyMongo) or `sample.csv` depending on `DATA_SOURCE`.
* **CSV/Mongo Data Linkage:** Each variant record carries a `sample_id` field that links it to the matching sample record, so the variants shown for a sample are exactly the ones tied to that `sample_id` — whether the data comes from the CSV files or MongoDB.
* **Interactive Visualization:** Integrates **Bokeh** to render quality score vs. allele frequency scatter plots with interactive hover inspections.
* **Resilient Fallback Mode:** When `DATA_SOURCE = "mongodb"`, a built-in connection health-check automatically serves sample and variant data loaded from the CSV files, with UI status badging, if the live MongoDB instance is unreachable.
* **Auto-Refresh on Migrate:** In `"csv"` mode, every time `python manage.py migrate` is run, the app re-reads `variants.csv` and refreshes the `Gene`/`Variant` tables to match it (adding, updating, and removing rows as needed) — even when there are no pending schema migrations to apply. This means editing the CSV files and rerunning `migrate` is enough to update what's shown on the page.

---

## 2. Software Requirements & Dependencies

### **Core Stack**
* **Python:** `3.11`
* **Django:** `5.2.17`
* **Bokeh:** `3.9.2` (Interactive plotting and CDN asset integration)
* **PyMongo:** `>= 4.0` (MongoDB client driver)
* **psycopg2-binary:** `2.9.10` (PostgreSQL adapter for production database deployments)
* **Black & Flake8:** Python code formatting and PEP 8 compliance linting

### **Frontend Libraries (CDN-delivered)**
* **Bootstrap 5:** Responsive user interface and alert badges
* **jQuery 3.7.1 & DataTables 1.13.8:** Interactive sorting, pagination, and searching for variant tables
* **BokehJS 3.9.2:** Client-side vector rendering of scatter plots

---

## 3. Installation & Setup

### **Step 1: Clone the Repository & Setup Conda**
Create and activate the isolated Conda environment using `environment.yml`:

```bash
# Create environment from YAML specification
conda env create -f environment.yml

# Activate environment
conda activate variantdb
```

*If updating an existing environment:*
```bash
conda env update --file environment.yml --prune
```

---

### **Step 2: Apply Database Migrations**
Initialize the relational schema and seed initial variant records from `variants/data/variants.csv`:

```bash
python manage.py migrate
```

`python manage.py migrate` always re-syncs the `Gene`/`Variant` tables against the current contents of `variants/data/variants.csv` — not just on first run. To update the variants shown on the site, edit `variants/data/variants.csv` and rerun `python manage.py migrate`; no other command is needed. The same applies to sample tracking data: edit `variants/data/sample.csv` and refresh the page (no migration required, since sample data is read directly at request time).

This describes the default `DATA_SOURCE = "csv"` mode. To read sample and variant data from MongoDB instead, see Section 4.

---

### **Step 3: Run the Development Server**
Launch the Django server:

```bash
python manage.py runserver
```

Open your browser and navigate to **`http://127.0.0.1:8000/`**.

---

## 4. Choosing the Data Source: CSV vs. MongoDB

Both sample tracking data and genomic variant data can be read either from the local CSV files (`variants/data/sample.csv` and `variants/data/variants.csv`) or from a live MongoDB instance. Which one is used is controlled by a single setting.

### **4.1. The `DATA_SOURCE` Switch**
In `variantdb/settings.py`:

```python
# Data Source Toggle: choose where sample & variant data is read from.
#   "csv"      -> read from variants/data/sample.csv and variants/data/variants.csv
#   "mongodb"  -> read from the MongoDB collections configured below
DATA_SOURCE = "csv"
```

* `"csv"` (default) — samples are read from `sample.csv`, and variants are read from the SQL `Gene`/`Variant` tables, which are kept in sync with `variants.csv` on every `python manage.py migrate` (see Section 5.1).
* `"mongodb"` — samples are read from the `samples` collection and variants from the `variants` collection in the MongoDB database configured below, for every sample regardless of its `Completed` / `In Progress` / `QC Warning` status. If the MongoDB connection fails, the app falls back to the CSV files for that request and displays a clear "MongoDB is unavailable" banner at the top of the page, plus a red "MongoDB Unavailable — Showing CSV Data" badge on the affected table(s), so it's never silently swapped out.

This logic lives in `variants/mongo.py`, in `get_sample_tracking_data()` (samples) and `get_variants_for_sample()` (variants). Both functions return a `(data, source)` tuple, where `source` is one of `"mongodb"`, `"csv"`, or `"mongodb_unavailable"` — `views.py` passes these through to the template so the correct badge and banner are shown for whichever data was actually served on that request.

### **4.2. Setting Connection Details Without Hardcoding Credentials**
`variantdb/settings.py` never contains a MongoDB username or password. Instead, the host, credentials, and database name are supplied as separate environment variables and assembled into the connection URI at runtime:

```python
MONGO_HOST = os.environ.get("MONGO_HOST", "localhost:27017")
MONGO_USER = os.environ.get("MONGO_USER", "")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", "")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "sample_tracking_db")

if MONGO_USER:
    from urllib.parse import quote_plus

    MONGO_URI = (
        f"mongodb+srv://{quote_plus(MONGO_USER)}:{quote_plus(MONGO_PASSWORD)}"
        f"@{MONGO_HOST}/"
    )
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}/"
```

Set these as environment variables (for local development, put them in a `.env` file — already listed in `.gitignore` so it's never committed — and load it with a tool like `python-dotenv`, or export them in your shell):

| Variable | Purpose | Required? |
| :--- | :--- | :--- |
| `MONGO_HOST` | Host or SRV address only, e.g. `cluster0.abcde.mongodb.net` — never include credentials here. | No (defaults to `localhost:27017`) |
| `MONGO_USER` | Database username. | No — omit for an unauthenticated local MongoDB |
| `MONGO_PASSWORD` | Database password. Special characters are automatically URL-encoded. | No — omit if `MONGO_USER` is omitted |
| `MONGO_DB_NAME` | Target database name. | No (defaults to `sample_tracking_db`) |

If `MONGO_USER` is not set, an unauthenticated `mongodb://` URI is built from `MONGO_HOST` — suitable for local development against an unauthenticated MongoDB instance. In production, or your deployment platform's secrets manager, inject `MONGO_USER` / `MONGO_PASSWORD` as secrets rather than committing them anywhere in the repository.

These settings are only used when `DATA_SOURCE = "mongodb"`.

### **4.3. Adjusting Collection Names & Network Timeout**
In `variants/mongo.py`:

1. **Target Collections:** Modify `db.samples` (in `_load_samples_from_mongo`) and `db.variants` (in `get_variants_for_sample`) to your target collection names if different (e.g., `db["clinical_samples"]`).
2. **Network Timeout:** Increase `serverSelectionTimeoutMS` from `1000` (1s local fallback) to `5000` (5s) for remote cloud clusters (e.g., MongoDB Atlas). This value appears in both `_load_samples_from_mongo` and `get_variants_for_sample`.

```python
# In variants/mongo.py
client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
```

### **4.4. Expected MongoDB Document Shapes**
When `DATA_SOURCE = "mongodb"`, documents in the `samples` collection should follow the same shape described in Section 5.2 (minus the CSV-specific pipe-delimiting — use real arrays for `completed_steps`, `pending_steps`, and `qc_tests.passed` / `qc_tests.failed`). Documents in the `variants` collection should have one document per variant, with fields `sample_id`, `symbol`, `chromosome`, `position`, `ref_allele`, `alt_allele`, `allele_frequency`, and `quality_score` — matching the columns of `variants.csv` (Section 5.1).

---

## 5. Database Schema & Data Models

### **5.1. Relational SQL Model (`variants/models.py`)**
| Table / Model | Field | Type | Description |
| :--- | :--- | :--- | :--- |
| **`Gene`** | `symbol` | `CharField(10)` | Gene identifier (e.g., *BRCA1*, *EGFR*, *TP53*) |
| | `chromosome` | `CharField(2)` | Chromosomal location (e.g., `17`, `7`, `12`) |
| **`Variant`** | `gene` | `ForeignKey(Gene)` | Relationship to annotated gene record |
| | `sample_id` | `CharField(64)` | Identifier of the sample this variant belongs to (links to `sample.csv`) |
| | `position` | `PositiveIntegerField` | Genomic coordinate position |
| | `ref_allele` | `CharField(10)` | Reference allele sequence |
| | `alt_allele` | `CharField(10)` | Alternate/variant allele sequence |
| | `allele_frequency` | `FloatField` | Population/sample allele frequency |
| | `quality_score` | `FloatField` | Phred-scaled variant calling quality score |

The `Gene` and `Variant` tables are populated and kept in sync from `variants/data/variants.csv`, which has one row per variant:

```csv
sample_id,symbol,chromosome,position,ref_allele,alt_allele,allele_frequency,quality_score
SMP-2026-001,BRCA1,17,43094692,G,A,0.0021,58.3
```

The `sample_id` column links each variant to the sample it was called from — it must match a `sample_id` value in `sample.csv` (Section 5.2) for the linkage to resolve on the sample detail page.

---

### **5.2. Sample Tracking Data (`variants/data/sample.csv`)**
Sample tracking records — normally served from MongoDB — are read from `variants/data/sample.csv` whenever MongoDB is unreachable (see Section 4), and this is the only data source used in local development without a MongoDB instance. Each row is one sample:

| Column | Description |
| :--- | :--- |
| `sample_id` | Unique sample identifier, e.g. `SMP-2026-001`. Referenced by `variants.csv`. |
| `patient_id` | Associated patient identifier. |
| `gene_panel` | Name of the clinical gene panel used. |
| `status` | One of `Completed`, `In Progress`, or `QC Warning`; determines which detail view is shown. |
| `sequencing_depth` | Mean sequencing depth, e.g. `120x`. |
| `current_step` | Optional. The pipeline stage currently in progress or flagged. |
| `completed_steps` | Pipe-delimited (`\|`) list of finished pipeline steps. |
| `pending_steps` | Pipe-delimited (`\|`) list of remaining or active pipeline steps. |
| `qc_passed` | Pipe-delimited (`\|`) list of passed QC checks. |
| `qc_failed` | Pipe-delimited (`\|`) list of failed QC checks. |

Example row (`Completed` sample):

```csv
sample_id,patient_id,gene_panel,status,sequencing_depth,current_step,completed_steps,pending_steps,qc_passed,qc_failed
SMP-2026-001,PAT-1082,Hypertrophic Cardiomyopathy (HCM),Completed,120x,,"Sample Accessioning & DNA Extraction|Library Preparation & Indexing",,"DNA Integrity Score (DIN: 8.5 / 10)|Mean Target Coverage (120x ≥ 30x threshold)",
```

`variants/mongo.py` parses this file into the same document shape the app would otherwise receive from MongoDB, so the rest of the application (views and templates) doesn't need to know whether a sample came from MongoDB or from the CSV fallback.

---

## 6. Sample Tracking Workflows & UI States

The application dashboard provides dynamic views based on the selected sample status:

```
+-------------------------------------------------------------------------+
|                      MongoDB Sample Tracking Table                      |
|  [SMP-2026-001 (Completed)]  [SMP-2026-002 (In Progress)]  [SMP-003 (QC)]|
+-------------------------------------------------------------------------+
                                     |
         +---------------------------+---------------------------+
         |                                                       |
         v                                                       v
+-----------------------------+             +-----------------------------+
|    Status: Completed        |             | Status: In Progress / QC    |
|-----------------------------|             |-----------------------------|
| * Bokeh Quality Plot        |             | * Pipeline Stage Checklist  |
| * Interactive Variant Table |             | * Passed vs Failed QC Tests |
+-----------------------------+             +-----------------------------+
```

### **1. `Completed` State (e.g., `SMP-2026-001`)**
* **Trigger:** User clicks **Select Sample** on a sample with status `Completed`.
* **Display:**
  * **Interactive Bokeh Scatter Plot:** Visualizes variant allele frequency ($X$-axis) against variant quality score ($Y$-axis) with custom tooltips.
  * **Genomic Variants Table:** DataTables-enabled view of all associated variants with live search, pagination, and multi-column sorting.

### **2. `In Progress` State (e.g., `SMP-2026-002`)**
* **Trigger:** User clicks **Select Sample** on a sample undergoing active processing.
* **Display:** A step-by-step pipeline audit card displaying:
  * **Completed Steps (Green):** Accessioning, DNA extraction, library preparation, enrichment, and sequencing.
  * **Active & Pending Steps (Blue/Gray):** Current pipeline stage (e.g., `Bioinformatics Alignment & Variant Calling (Running)`), QA verification, and report generation.

### **3. `QC Warning` State (e.g., `SMP-2026-003`)**
* **Trigger:** User clicks **Select Sample** on a flagged sample.
* **Display:** A QC diagnostic analysis card outlining failure thresholds:
  * **Failed Checks (Red):** Flags specific sub-threshold lab metrics (e.g., `Mean Target Coverage: 28x (Min: 30x)` and `Uniformity of Coverage at 20x: 68.2% (Target: ≥ 80%)`).
  * **Passed Checks (Green):** Confirms passing parameters (e.g., `DIN Score: 8.2/10`, `Duplication Rate: 4.8%`, `Contamination: <0.2%`).

---

## 7. Project Structure

```text
variantdb_mongodb/
├── environment.yml                  # Conda environment definition (Python 3.11, Django, PyMongo, Bokeh)
├── requirements.txt                 # Pip dependency list
├── manage.py                        # Django management script
├── db.sqlite3                       # Relational database instance
├── variantdb/                       # Project configuration package
│   ├── settings.py                  # App configuration & MongoDB connection variables
│   ├── urls.py                      # Root URL routing
│   ├── wsgi.py                      # WSGI production gateway
│   └── asgi.py                      # ASGI async gateway
└── variants/                        # Variants application
    ├── models.py                    # Gene and Variant relational ORM models
    ├── mongo.py                     # DATA_SOURCE-aware loaders: MongoDB clients + CSV fallback for samples & variants
    ├── data_sync.py                 # Syncs variants.csv into the Gene/Variant tables
    ├── views.py                     # Dashboard business logic & Bokeh plot generation
    ├── urls.py                      # App-level routing
    ├── apps.py                      # App config; re-syncs variants.csv on every migrate
    ├── data/                        # CSV data files (single source of truth for content)
    │   ├── variants.csv             # Genomic variants, one row each, linked via sample_id
    │   └── sample.csv               # Sample tracking, pipeline, and QC records
    ├── migrations/                  # Database migration history & seed scripts
    └── templates/variants/          # Jinja/Django template files
        ├── base.html                # Global HTML shell (Bootstrap, CDN loaders)
        └── variant_list.html        # Interactive sample tracking, Bokeh chart, & variant tables
```

---

## 8. Code Quality & Formatting

To ensure compliance with PEP 8 standards:

```bash
# Format code with Black
black .

# Check linting and style errors with Flake8
flake8 .
```
