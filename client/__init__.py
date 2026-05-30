"""
Python client library for the Roman Urdu Normalizer API.

Lets users call the API without writing raw HTTP code:

    from client import RomanUrduNormalizerClient

    client = RomanUrduNormalizerClient("http://localhost:8000")
    result = client.normalize("yr bht thora kya")
    print(result["normalized"])

The client adds retries, timeout handling, and batch helpers — things
nobody wants to redo every time they call an API.

Author: Mughirah Nasir, 2026.
"""

from client.normalizer_client import (
    RomanUrduNormalizerClient,
    NormalizerClientError,
    NormalizerAPIError,
    NormalizerTimeout,
)

__version__ = "1.0.0"
__all__ = [
    "RomanUrduNormalizerClient",
    "NormalizerClientError",
    "NormalizerAPIError",
    "NormalizerTimeout",
    "__version__",
]
