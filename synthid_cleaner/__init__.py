"""
SynthID Cleaner - Sanitize AI-generated images by stripping C2PA metadata
and disrupting imperceptible SynthID watermarks.
"""

from .core import sanitize_image, batch_sanitize

__version__ = "1.0.0"
__all__ = ["sanitize_image", "batch_sanitize", "__version__"]
