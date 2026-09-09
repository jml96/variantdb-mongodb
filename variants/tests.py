from django.test import TestCase

from .models import Gene, Variant


class VariantListViewTests(TestCase):
    def setUp(self):
        self.gene = Gene.objects.create(symbol="TESTGENE", chromosome="1")
        Variant.objects.create(
            gene=self.gene,
            position=12345,
            ref_allele="A",
            alt_allele="G",
            allele_frequency=0.05,
            quality_score=99.9,
        )

    def test_variant_list_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_variant_list_shows_gene_and_variant_data(self):
        response = self.client.get("/")
        content = response.content.decode()
        self.assertIn("TESTGENE", content)
        self.assertIn("variant-table", content)

    def test_bokeh_plot_is_embedded(self):
        response = self.client.get("/")
        content = response.content.decode()
        self.assertIn("Bokeh", content)

    def test_seed_data_migration_created_sample_genes(self):
        # Sample data created by the 0002_seed_sample_data migration
        self.assertTrue(Gene.objects.filter(symbol="BRCA1").exists())
        self.assertTrue(Gene.objects.filter(symbol="TP53").exists())
