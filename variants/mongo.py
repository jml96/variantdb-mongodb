"""MongoDB connection and sample tracking helper."""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Fallback simulated records with enriched progress and QC details
SIMULATED_SAMPLES = [
    {
        "sample_id": "SMP-2026-001",
        "patient_id": "PAT-1082",
        "gene_panel": "Hypertrophic Cardiomyopathy (HCM)",
        "status": "Completed",
        "sequencing_depth": "120x",
        "completed_steps": [
            "Sample Accessioning & DNA Extraction",
            "Library Preparation & Indexing",
            "Target Enrichment & Hybridization",
            "Illumina High-Throughput Sequencing",
            "Bioinformatics Alignment & Variant Calling",
            "Quality Assurance Verification",
        ],
        "pending_steps": [],
        "qc_tests": {
            "passed": [
                "DNA Integrity Score (DIN: 8.5 / 10)",
                "Mean Target Coverage (120x ≥ 30x threshold)",
                "Target Base Coverage at 20x (99.4%)",
                "Library Duplication Rate (3.1% ≤ 10%)",
                "Sample Contamination Rate (< 0.1%)",
            ],
            "failed": [],
        },
    },
    {
        "sample_id": "SMP-2026-002",
        "patient_id": "PAT-1099",
        "gene_panel": "Rare Heart & Lung Diseases",
        "status": "In Progress",
        "sequencing_depth": "95x",
        "current_step": "Bioinformatics Alignment & Variant Calling",
        "completed_steps": [
            "Sample Accessioning & DNA Extraction",
            "Library Preparation & Indexing",
            "Target Enrichment & Hybridization",
            "Illumina High-Throughput Sequencing",
        ],
        "pending_steps": [
            "Bioinformatics Alignment & Variant Calling (Running)",
            "Quality Assurance Verification",
            "Final Clinical Report Generation",
        ],
        "qc_tests": {
            "passed": [
                "DNA Integrity Score (DIN: 7.9 / 10)",
                "Library Prep Fluorometric Qubit Yield (Pass)",
            ],
            "failed": [],
        },
    },
    {
        "sample_id": "SMP-2026-003",
        "patient_id": "PAT-2041",
        "gene_panel": "Familial Arrhythmia",
        "status": "QC Warning",
        "sequencing_depth": "28x",
        "current_step": "Quality Assurance Verification (Flagged)",
        "completed_steps": [
            "Sample Accessioning & DNA Extraction",
            "Library Preparation & Indexing",
            "Target Enrichment & Hybridization",
            "Illumina High-Throughput Sequencing",
            "Bioinformatics Alignment & Variant Calling",
        ],
        "pending_steps": [
            "Quality Assurance Verification (On Hold)",
            "Final Clinical Report Generation",
        ],
        "qc_tests": {
            "passed": [
                "DNA Integrity Score (DIN: 8.2 / 10)",
                "Library Duplication Rate (4.8% ≤ 10%)",
                "Sample Contamination Rate (< 0.2%)",
            ],
            "failed": [
                "Mean Target Coverage (28x — Minimum required: 30x)",
                "Uniformity of Coverage at 20x (68.2% — Target: ≥ 80.0%)",
            ],
        },
    },
]


def get_sample_tracking_data():
    """Fetches sample records from MongoDB.

    Falls back to simulated data if MongoDB is unreachable or offline.
    Returns: (list_of_samples, is_simulated_boolean)
    """
    try:
        from pymongo import MongoClient

        # Fast 1-second connection timeout check
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=1000)
        client.admin.command("ping")

        db = client[settings.MONGO_DB_NAME]
        samples = list(db.samples.find({}, {"_id": 0}))

        if samples:
            return samples, False
    except Exception as exc:
        logger.warning(
            f"MongoDB connection unavailable ({exc}). Using simulated sample tracking data."
        )

    return SIMULATED_SAMPLES, True