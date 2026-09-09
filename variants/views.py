"""Views for the variants app."""

from bokeh.embed import components
from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.resources import CDN
from django.shortcuts import render

from .mongo import (
    SOURCE_MONGODB_UNAVAILABLE,
    get_sample_tracking_data,
    get_variants_for_sample,
)


def variant_list(request):
    """Displays sample tracking data by default (source set by settings.DATA_SOURCE).

    When a completed sample is selected via query parameter (`?sample_id=...`),
    loads its genomic variants and renders the interactive Bokeh scatter plot.
    """
    samples, samples_source = get_sample_tracking_data()

    selected_sample_id = request.GET.get("sample_id")
    selected_sample = None
    variants = None
    variants_source = None
    script, div = None, None

    # Identify selected sample from URL query parameter
    if selected_sample_id:
        for sample in samples:
            if sample.get("sample_id") == selected_sample_id:
                selected_sample = sample
                break

    # Only load variants and generate Bokeh plot if status is Completed
    if selected_sample and selected_sample.get("status") == "Completed":
        variants, variants_source = get_variants_for_sample(
            selected_sample.get("sample_id")
        )
        if variants:
            plot = _build_quality_vs_frequency_plot(variants)
            script, div = components(plot)

    mongo_unavailable = (
        samples_source == SOURCE_MONGODB_UNAVAILABLE
        or variants_source == SOURCE_MONGODB_UNAVAILABLE
    )

    context = {
        "samples": samples,
        "selected_sample": selected_sample,
        "selected_sample_id": selected_sample_id,
        "variants": variants,
        "samples_source": samples_source,
        "variants_source": variants_source,
        "mongo_unavailable": mongo_unavailable,
        "bokeh_script": script,
        "bokeh_div": div,
        "bokeh_css_files": CDN.css_files,
        "bokeh_js_files": CDN.js_files,
    }
    return render(request, "variants/variant_list.html", context)


def _build_quality_vs_frequency_plot(variants):
    """Build a Bokeh scatter plot of quality score vs. allele frequency."""
    allele_frequencies = [v.allele_frequency for v in variants]
    quality_scores = [v.quality_score for v in variants]
    labels = [str(v) for v in variants]

    source_data = dict(
        x=allele_frequencies,
        y=quality_scores,
        label=labels,
    )

    plot = figure(
        title="Variant Quality Score vs. Allele Frequency",
        x_axis_label="Allele Frequency",
        y_axis_label="Quality Score",
        height=400,
        sizing_mode="stretch_width",
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )
    scatter_renderer = plot.scatter(
        "x",
        "y",
        source=source_data,
        size=10,
        fill_alpha=0.7,
        color="#0d6efd",
    )
    plot.add_tools(
        HoverTool(
            renderers=[scatter_renderer],
            tooltips=[("Variant", "@label"), ("AF", "@x"), ("QUAL", "@y")],
        )
    )
    return plot