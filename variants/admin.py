from django.contrib import admin

from .models import Gene, Variant


class VariantInline(admin.TabularInline):
    """Inline editor so variants can be added directly under a gene."""

    model = Variant
    extra = 1


@admin.register(Gene)
class GeneAdmin(admin.ModelAdmin):
    list_display = ("symbol", "chromosome")
    search_fields = ("symbol",)
    inlines = [VariantInline]


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = (
        "gene",
        "position",
        "ref_allele",
        "alt_allele",
        "allele_frequency",
        "quality_score",
    )
    list_filter = ("gene",)
