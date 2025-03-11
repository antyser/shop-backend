"""Evaluation modules for reviewing model outputs."""

from app.llm.evals.review_evaluator import (
    coverage_evaluator,
    evaluate_extraction,
    factuality_evaluator,
)

# Remove imports from review_extractor to resolve circular dependencies
# Import these in the specific modules that need them instead

__all__ = [
    # Functions imported from elsewhere but exposed in this API
    "extract_reviews",
    "evaluate_extraction",
    "process_file",
    "process_batch",
    "merge_reviews",
    "process_and_merge_files",
    "review_merger",
    # Functions defined in this module
    "factuality_evaluator",
    "coverage_evaluator",
]
