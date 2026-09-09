from django.db import migrations

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

    dependencies = [
        ("variants", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, remove_seed_data),
    ]
