"""Mask loading and analysis helpers."""

from titanforge.masks.analyzer import MaskAnalysis, analyze_png_mask, format_mask_analysis
from titanforge.masks.classifier import MaskColorClassifier
from titanforge.masks.coastline import CoastlineSmoothingResult, render_coastline_smoothing_preview
from titanforge.masks.cleanup import MaskCleanupResult, render_mask_cleanup_preview
from titanforge.masks.demo import DemoMaskResult, generate_demo_mask
from titanforge.masks.palette import DEFAULT_ZONE_PALETTE, MaskColor, ZoneDefinition

__all__ = [
    "CoastlineSmoothingResult",
    "DEFAULT_ZONE_PALETTE",
    "DemoMaskResult",
    "MaskCleanupResult",
    "MaskAnalysis",
    "MaskColorClassifier",
    "MaskColor",
    "ZoneDefinition",
    "analyze_png_mask",
    "generate_demo_mask",
    "render_coastline_smoothing_preview",
    "render_mask_cleanup_preview",
    "format_mask_analysis",
]
