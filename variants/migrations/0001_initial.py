import django.db.models.deletion
from django.db import migrations, models

from variants.data_sync import sync_variants_from_csv


def seed_data(apps, schema_editor):
    gene_model = apps.get_model("variants", "Gene")
    variant_model = apps.get_model("variants", "Variant")
    sync_variants_from_csv(gene_model, variant_model)


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
                    "sample_id",
                    models.CharField(
                        help_text="Identifier of the sample this variant belongs to (links to sample.csv).",
                        max_length=64,
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