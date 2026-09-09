import csv
from pathlib import Path
import django.db.models.deletion
from django.db import migrations, models


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

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Gene",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "symbol",
                    models.CharField(
                        help_text="HGNC-style gene symbol, e.g. BRCA1.",
                        max_length=32,
                        unique=True,
                    ),
                ),
                ("chromosome", models.CharField(max_length=8)),
            ],
            options={
                "ordering": ["symbol"],
            },
        ),
        migrations.CreateModel(
            name="Variant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "position",
                    models.PositiveIntegerField(help_text="Genomic position (bp)."),
                ),
                (
                    "ref_allele",
                    models.CharField(max_length=16, verbose_name="Reference allele"),
                ),
                (
                    "alt_allele",
                    models.CharField(max_length=16, verbose_name="Alternate allele"),
                ),
                (
                    "allele_frequency",
                    models.FloatField(help_text="Population allele frequency (0-1)."),
                ),
                (
                    "quality_score",
                    models.FloatField(help_text="Variant call quality score."),
                ),
                (
                    "gene",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variants",
                        to="variants.gene",
                    ),
                ),
            ],
            options={
                "ordering": ["gene__symbol", "position"],
            },
        ),
        migrations.RunPython(seed_data, remove_seed_data),
    ]