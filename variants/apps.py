from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


def _refresh_variants_from_csv(sender, **kwargs):
    """Re-syncs the Gene/Variant tables from variants.csv after every migrate.

    Skipped when settings.DATA_SOURCE is "mongodb", since variants are then
    read directly from MongoDB and the SQL tables are not used.
    """
    if getattr(settings, "DATA_SOURCE", "csv") == "mongodb":
        return

    from .data_sync import sync_variants_from_csv

    gene_model = sender.get_model("Gene")
    variant_model = sender.get_model("Variant")
    sync_variants_from_csv(gene_model, variant_model)


class VariantsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "variants"

    def ready(self):
        post_migrate.connect(_refresh_variants_from_csv, sender=self)
