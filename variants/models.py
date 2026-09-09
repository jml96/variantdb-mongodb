"""Models for the variants app.

Defines two linked tables:
    Gene    -- the "one" side of a one-to-many relationship.
    Variant -- the "many" side; each Variant belongs to exactly one Gene.
"""

from django.db import models


class Gene(models.Model):
    """A gene that one or more variants can be associated with."""

    symbol = models.CharField(
        max_length=32,
        unique=True,
        help_text="HGNC-style gene symbol, e.g. BRCA1.",
    )
    chromosome = models.CharField(max_length=8)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return self.symbol


class Variant(models.Model):
    """A single genomic variant linked to one gene (many-to-one)."""

    gene = models.ForeignKey(
        Gene,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    sample_id = models.CharField(
        max_length=64,
        help_text="Identifier of the sample this variant belongs to (links to sample.csv).",
    )
    position = models.PositiveIntegerField(help_text="Genomic position (bp).")
    ref_allele = models.CharField(max_length=16, verbose_name="Reference allele")
    alt_allele = models.CharField(max_length=16, verbose_name="Alternate allele")
    allele_frequency = models.FloatField(help_text="Population allele frequency (0-1).")
    quality_score = models.FloatField(help_text="Variant call quality score.")

    class Meta:
        ordering = ["gene__symbol", "position"]

    def __str__(self):
        return f"{self.gene.symbol}:{self.position}{self.ref_allele}>{self.alt_allele}"
