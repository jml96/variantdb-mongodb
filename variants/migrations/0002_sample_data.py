import csv
from pathlib import Path
from django.db import migrations


def seed_data(apps, schema_editor):
    gene_model = apps.get_model("variants", "Gene")
    variant_model = apps.get_model("variants", "Variant")

    # Locate the CSV file inside variants/data/variants.csv
    file_path = Path(__file__).resolve().parent.parent / "data" / "variants.csv"

    if not file_path.exists():
        return

    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Get or create the parent Gene
            gene, _ = gene_model.objects.get_or_create(
                symbol=row["symbol"].strip(),
                defaults={"chromosome": row["chromosome"].strip()},
            )

            # Create the Variant linked to that Gene
            variant_model.objects.get_or_create(
                gene=gene,
                position=int(row["position"]),
                ref_allele=row["ref_allele"].strip(),
                alt_allele=row["alt_allele"].strip(),
                allele_frequency=float(row["allele_frequency"]),
                quality_score=float(row["quality_score"]),
            )


def remove_seed_data(apps, schema_editor):
    gene_model = apps.get_model("variants", "Gene")
    # Clean up created genes/variants on reverse migration
    gene_model.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("variants", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, remove_seed_data),
    ]