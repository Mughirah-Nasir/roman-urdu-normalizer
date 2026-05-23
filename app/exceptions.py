"""
Custom exception hierarchy for the Roman Urdu Normalizer.

A flat tree, but it's a tree on purpose: it lets callers catch all
normalizer errors with one except clause if they want to, while still
allowing fine-grained handling of specific failure modes.

    NormalizerError                <- base; catch this for anything from us
    ├── InvalidInputError          <- malformed text / wrong shape
    ├── DictionaryIntegrityError   <- the data layer is internally inconsistent
    └── BatchSizeError             <- batch endpoint over the limit

We don't raise these for "word not found" — that's not an error, it's the
"unknown" branch of the normal resolution flow.
"""


class NormalizerError(Exception):
    """Base class for any error raised by the normalizer package."""
    pass


class InvalidInputError(NormalizerError):
    """Input text is malformed or violates basic shape constraints."""
    pass


class DictionaryIntegrityError(NormalizerError):
    """The lexicon / variant map / homograph groups are inconsistent.

    Example: a homograph group references a word that isn't in the canonical
    lexicon. Raised at module load time if the integrity check fails.
    """
    pass


class BatchSizeError(NormalizerError):
    """Batch request exceeded the configured maximum item count."""

    def __init__(self, n: int, limit: int):
        self.n = n
        self.limit = limit
        super().__init__(
            f"Batch size {n} exceeds maximum allowed ({limit}). "
            "Split the request into smaller batches."
        )
