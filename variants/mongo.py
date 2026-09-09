"""MongoDB connection and sample tracking helper."""

import csv
import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

# Location of the CSV file that holds all sample tracking data
SAMPLE_CSV_PATH = Path(__file__).resolve().parent / "data" / "sample.csv"

# Possible values returned as the "source" of a data fetch:
#   "mongodb"             -> served live from MongoDB
#   "csv"                 -> served from CSV because DATA_SOURCE = "csv"
#   "mongodb_unavailable" -> DATA_SOURCE = "mongodb" but the connection
#                            failed; CSV data is being served as a fallback
SOURCE_MONGODB = "mongodb"
SOURCE_CSV = "csv"
SOURCE_MONGODB_UNAVAILABLE = "mongodb_unavailable"


def _split_list_field(value):
    """Split a pipe-delimited CSV field into a list of strings."""
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def _load_samples_from_csv():
    """Loads sample tracking records from variants/data/sample.csv."""
    if not SAMPLE_CSV_PATH.exists():
        return []

    samples = []
    with open(SAMPLE_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = {
                "sample_id": row["sample_id"].strip(),
                "patient_id": row["patient_id"].strip(),
                "gene_panel": row["gene_panel"].strip(),
                "status": row["status"].strip(),
                "sequencing_depth": row["sequencing_depth"].strip(),
                "completed_steps": _split_list_field(row.get("completed_steps", "")),
                "pending_steps": _split_list_field(row.get("pending_steps", "")),
                "qc_tests": {
                    "passed": _split_list_field(row.get("qc_passed", "")),
                    "failed": _split_list_field(row.get("qc_failed", "")),
                },
            }

            current_step = row.get("current_step", "").strip()
            if current_step:
                sample["current_step"] = current_step

            samples.append(sample)

    return samples


def _get_mongo_db():
    """Opens a MongoDB connection and returns the configured database.

    Raises if MongoDB is unreachable; callers are responsible for
    catching this and falling back to CSV data.
    """
    from pymongo import MongoClient

    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=1000)
    client.admin.command("ping")
    return client[settings.MONGO_DB_NAME]


def _load_samples_from_mongo():
    """Loads sample tracking records from the MongoDB `samples` collection."""
    db = _get_mongo_db()
    return list(db.samples.find({}, {"_id": 0}))


class _MongoGene:
    """Minimal stand-in for the Gene model, used for Mongo-sourced variants."""

    def __init__(self, symbol, chromosome):
        self.symbol = symbol
        self.chromosome = chromosome


class MongoVariant:
    """Minimal stand-in for the Variant model, used when DATA_SOURCE is
    "mongodb". Exposes the same attributes the template and Bokeh plot
    code use (gene.symbol, gene.chromosome, position, ref_allele,
    alt_allele, allele_frequency, quality_score) so both can render
    Mongo-sourced variants without any changes.
    """

    def __init__(self, doc):
        self.sample_id = doc.get("sample_id")
        self.gene = _MongoGene(doc.get("symbol"), doc.get("chromosome"))
        self.position = doc.get("position")
        self.ref_allele = doc.get("ref_allele")
        self.alt_allele = doc.get("alt_allele")
        self.allele_frequency = doc.get("allele_frequency")
        self.quality_score = doc.get("quality_score")

    def __str__(self):
        return f"{self.gene.symbol}:{self.position}{self.ref_allele}>{self.alt_allele}"


def get_variants_for_sample(sample_id):
    """Fetches variants for a sample from the source configured in
    settings.DATA_SOURCE ("csv" or "mongodb").

    "csv" reads from the SQL tables (kept in sync with variants.csv via
    the post_migrate signal in apps.py). "mongodb" queries the `variants`
    collection directly and wraps each document in MongoVariant so the
    caller can treat both sources identically.

    Returns: (list_of_variants, source) where source is one of
    SOURCE_MONGODB, SOURCE_CSV, or SOURCE_MONGODB_UNAVAILABLE.
    """
    if settings.DATA_SOURCE == "mongodb":
        try:
            db = _get_mongo_db()
            docs = db.variants.find({"sample_id": sample_id}, {"_id": 0})
            return [MongoVariant(doc) for doc in docs], SOURCE_MONGODB
        except Exception as exc:
            logger.warning(
                f"MongoDB connection unavailable ({exc}). "
                "Falling back to variant data from variants.csv."
            )
            from .models import Variant

            variants = list(
                Variant.objects.select_related("gene").filter(sample_id=sample_id)
            )
            return variants, SOURCE_MONGODB_UNAVAILABLE

    from .models import Variant

    variants = list(
        Variant.objects.select_related("gene").filter(sample_id=sample_id)
    )
    return variants, SOURCE_CSV


def get_sample_tracking_data():
    """Fetches sample tracking records from the source configured in
    settings.DATA_SOURCE ("csv" or "mongodb").

    Returns: (list_of_samples, source) where source is one of
    SOURCE_MONGODB, SOURCE_CSV, or SOURCE_MONGODB_UNAVAILABLE.
    """
    if settings.DATA_SOURCE == "mongodb":
        try:
            samples = _load_samples_from_mongo()
            return samples, SOURCE_MONGODB
        except Exception as exc:
            logger.warning(
                f"MongoDB connection unavailable ({exc}). "
                "Falling back to sample tracking data from sample.csv."
            )
            return _load_samples_from_csv(), SOURCE_MONGODB_UNAVAILABLE

    # settings.DATA_SOURCE == "csv" (default)
    return _load_samples_from_csv(), SOURCE_CSV
