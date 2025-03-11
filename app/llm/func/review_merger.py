"""Functions for merging multiple review analysis files into comprehensive summaries."""

import argparse
import asyncio
from pathlib import Path
from typing import List, Optional

from loguru import logger

from app.llm.constants import O3_MINI_MODEL
from app.llm.func.review_extractor import merge_reviews


async def review_merger(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    product_name: str = None,
    model_name: str = O3_MINI_MODEL,
    file_pattern: str = "*.analysis.txt",
    output_format: str = "structured",
    token_limit: Optional[int] = None,
) -> Path:
    """
    Merge multiple review analysis files into a comprehensive product summary.

    This function directly reads existing analysis files and merges them into a
    single, coherent product summary that helps users make purchase decisions.
    It skips the extraction phase since the reviews have already been analyzed.

    Args:
        input_dir: Directory containing the analysis files
        output_dir: Directory to save the merged summary (defaults to input_dir)
        product_name: Name of the product being reviewed (required)
        model_name: Name of the model to use for merging
        file_pattern: Glob pattern for files to process
        output_format: Format of the output summary - "structured" or "narrative"
        token_limit: Optional maximum token limit for the summary

    Returns:
        Path to the merged summary file
    """
    if not product_name:
        raise ValueError("Product name is required for merging reviews")

    # Create output directory if needed
    output_dir = output_dir or input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all analysis files
    analysis_files = list(input_dir.glob(file_pattern))
    logger.info(f"Found {len(analysis_files)} analysis files to merge")

    if not analysis_files:
        logger.warning(f"No matching files found in {input_dir} using pattern '{file_pattern}'")
        return None

    # Read the content of each analysis file
    review_texts = []
    for file_path in analysis_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                review_texts.append(f.read())
            logger.info(f"Read {file_path.name}")
        except Exception as e:
            logger.error(f"Error reading {file_path.name}: {str(e)}")

    logger.info(f"Successfully read {len(review_texts)} analysis files")

    # Merge the reviews
    logger.info(f"Merging reviews for {product_name}...")
    merged_summary = await merge_reviews(
        review_texts=review_texts, model_name=model_name, product_name=product_name, token_limit=token_limit, output_format=output_format
    )

    # Create a clean product name for the filename
    clean_product_name = "".join(c if c.isalnum() else "_" for c in product_name)
    clean_product_name = clean_product_name.strip("_")

    # Create output file path
    output_file = output_dir / f"{clean_product_name}_merged_summary.txt"

    # Save the merged summary
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(merged_summary)

    logger.success(f"Merged summary saved to {output_file}")
    return output_file


async def main():
    """Run the review merger from the command line."""
    parser = argparse.ArgumentParser(description="Merge multiple review analysis files into a comprehensive summary")

    # Required arguments
    parser.add_argument("input_dir", type=Path, help="Directory containing the analysis files")
    parser.add_argument("--product-name", "-p", required=True, type=str, help="Name of the product being reviewed")

    # Optional arguments
    parser.add_argument("--output-dir", "-o", type=Path, help="Directory to save the merged summary")
    parser.add_argument("--model", "-m", default=O3_MINI_MODEL, help="Model to use for merging")
    parser.add_argument("--file-pattern", "-f", default="*.analysis.txt", help="Glob pattern for files to merge")
    parser.add_argument("--output-format", "-fmt", choices=["structured", "narrative"], default="structured", help="Format of the merged summary")
    parser.add_argument("--token-limit", "-t", type=int, help="Maximum token limit for the summary")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set log level based on verbose flag
    if args.verbose:
        logger.level("INFO")
    else:
        logger.level("SUCCESS")

    try:
        # Run the review merger
        await review_merger(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            product_name=args.product_name,
            model_name=args.model,
            file_pattern=args.file_pattern,
            output_format=args.output_format,
            token_limit=args.token_limit,
        )
        return 0
    except Exception as e:
        logger.error(f"Error merging reviews: {str(e)}")
        return 1


if __name__ == "__main__":
    asyncio.run(main())
