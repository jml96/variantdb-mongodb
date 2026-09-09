# variantdb

A small Django app built as the onboarding task: two linked models
(`Gene` → `Variant`, one-to-many), displayed as an interactive, sortable
table on the frontend, alongside a Bokeh scatter plot built from numerical
model data.

## 1. Install Miniconda

Skip this if conda is already installed.

**macOS / Linux:**
```bash
curl -L -O "https://repo.anaconda.com/miniconda/Miniconda3-latest-$(uname)-x86_64.sh"
bash Miniconda3-latest-$(uname)-x86_64.sh
# follow the prompts, then restart your terminal (or `source ~/.bashrc`)
```

**Windows:**
Download the installer from https://docs.conda.io/en/latest/miniconda.html
and run it, then open "Anaconda Prompt".

Verify it worked:
```bash
conda --version
```

## 2. Create the environment

From this project's root directory (where `environment.yml` lives):

```bash
conda env create -f environment.yml
conda activate variantdb
```

This creates a `variantdb` conda environment with Python 3.11, and installs
Django, Bokeh, the PostgreSQL adapter (`psycopg2-binary`), and `black` /
`flake8` for formatting and linting.

If you'd rather use plain `pip` inside an existing environment instead of
conda, `requirements.txt` is provided as an equivalent:
```bash
pip install -r requirements.txt
```

## 3. Set up the database

By default the project uses SQLite, so there's nothing to configure —
just run the migrations, which also seed a handful of example genes and
variants:

```bash
python manage.py migrate
```

**To use PostgreSQL instead** (matching the team's production setup):
1. Make sure a PostgreSQL server is running and you've created a database
   and user for this project.
2. Open `variantdb/settings.py`, comment out the default `DATABASES`
   block, and uncomment the PostgreSQL block just below it.
3. Set the corresponding environment variables (`DB_NAME`, `DB_USER`,
   `DB_PASSWORD`, `DB_HOST`, `DB_PORT`), or edit the defaults directly.
4. Run `python manage.py migrate` again.

## 4. Run the app

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ — you'll see a Bokeh scatter plot (quality
score vs. allele frequency) above a sortable table listing each variant
alongside its gene.

To explore/edit the data through Django's admin instead:
```bash
python manage.py createsuperuser   # follow the prompts
python manage.py runserver
# then visit http://127.0.0.1:8000/admin/
```

## 5. Run the tests

```bash
python manage.py test variants
```

## 6. Check code style

```bash
black --check variants/
flake8 --max-line-length=88 --exclude=migrations variants/ variantdb/
```

(Auto-generated files under `variants/migrations/` are excluded from the
line-length check, since Django writes those itself; `black --check`
still covers them and they are already formatted.)

## Project structure

```
variantdb/
├── environment.yml            # conda environment definition
├── requirements.txt           # pip equivalent
├── manage.py
├── variantdb/                 # project settings
│   ├── settings.py
│   └── urls.py
└── variants/                  # the app
    ├── models.py               # Gene (1) -> Variant (many)
    ├── admin.py                # admin registration, incl. inline editing
    ├── views.py                # builds the Bokeh plot, renders the table
    ├── urls.py
    ├── tests.py
    ├── migrations/
    │   ├── 0001_initial.py
    │   └── 0002_seed_sample_data.py   # example data, applied on migrate
    └── templates/variants/
        ├── base.html            # Bootstrap layout
        └── variant_list.html    # sortable table (DataTables) + Bokeh plot
```

## Design notes

- **Models**: `Gene` is the "one" side; `Variant` has a `ForeignKey` to
  `Gene` (the "many" side), matching the one-to-many requirement. The
  schema is fully defined through the models, as requested — nothing is
  created manually in the database.
- **Interactive, sortable table**: implemented with
  [DataTables](https://datatables.net/) (loaded via CDN, styled with
  Bootstrap 5) rather than a custom JS solution, since it's a
  well-established, accessible way to get client-side column sorting
  without adding a Python dependency.
- **Bokeh graph**: a scatter plot of `quality_score` vs.
  `allele_frequency` for all variants, embedded server-side with
  `bokeh.embed.components()`. The required BokehJS resources are pulled
  in dynamically via `bokeh.resources.CDN` so the JS version always
  matches the installed `bokeh` Python package.
- **Sample data**: seeded via a data migration (`0002_seed_sample_data`)
  rather than a fixture, so `python manage.py migrate` alone is enough to
  get a working, populated app — no separate `loaddata` step needed.
