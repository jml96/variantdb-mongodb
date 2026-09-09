"""Syncs the Variant/Gene SQL tables with variants/data/variants.csv.

This is called both from the initial migration (so a fresh database is
seeded) and from a post_migrate signal handler (so every subsequent
`python manage.py migrate` run re-reads the CSV and refreshes the
database, keeping the rendered HTML in sync with the CSV file).
"""

import csv
from pathlib import Path

VARIANTS_CSV_PATH = Path(__file__).resolve().parent / "data" / "variants.csv"


def sync_variants_from_csv(gene_model, variant_model, file_path=None):
    """Reads variants/data/variants.csv and syncs it into the Gene/Variant tables.

    Any gene/variant rows no longer present in the CSV are removed so the
    database always mirrors the current contents of the CSV file.
    """
    file_path = file_path or VARIANTS_CSV_PATH

    if not file_path.exists():
        return

    seen_variant_keys = []

    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row["symbol"].strip()
            sample_id = row["sample_id"].strip()
            position = int(row["position"])
            ref_allele = row["ref_allele"].strip()
            alt_allele = row["alt_allele"].strip()

            # Get or create the parent Gene, keeping chromosome up to date
            gene, _ = gene_model.objects.get_or_create(
                symbol=symbol,
                defaults={"chromosome": row["chromosome"].strip()},
            )
            if gene.chromosome != row["chromosome"].strip():
                gene.chromosome = row["chromosome"].strip()
                gene.save()

            # Create/update the Variant linked to that Gene and sample
            variant, _ = variant_model.objects.update_or_create(
                gene=gene,
                sample_id=sample_id,
                position=position,
                ref_allele=ref_allele,
                alt_allele=alt_allele,
                defaults={
                    "allele_frequency": float(row["allele_frequency"]),
                    "quality_score": float(row["quality_score"]),
                },
            )
            seen_variant_keys.append(variant.pk)

    # Remove variants that are no longer present in the CSV
    variant_model.objects.exclude(pk__in=seen_variant_keys).delete()

    # Remove genes that no longer have any variants pointing to them
    gene_model.objects.filter(variants__isnull=True).delete()
