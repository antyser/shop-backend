"""Models and functions for structured review analysis."""

import argparse
import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import logfire
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from tqdm import tqdm

from app.llm.constants import CLAUDE_SONNET_MODEL, O3_MINI_MODEL
from app.llm.evals.review_evaluator import evaluate_extraction
from app.llm.model_factory import create_model


async def extract_reviews(article_text: str, model_name: str, product_name: Optional[str] = None, token_limit: Optional[int] = None) -> str:
    """
    Analyze a product review article and extract structured information.

    Args:
        article_text: The text content of the review article
        model_name: Name of the model to use for analysis
        product_name: Optional name of the product being reviewed
        token_limit: Optional maximum token limit for the summary

    Returns:
        A string containing the extracted review summary
    """
    try:
        logger.info(f"Starting review article analysis using model: {model_name}")
        if product_name:
            logger.info(f"Extracting reviews for product: {product_name}")

        # Create appropriate model instance
        model = create_model(model_name)

        # Create agent with our result type
        agent = Agent(model=model, result_type=str)

        # Base prompt
        prompt = """**Role**: Meticulous analyst summarizing product reviews. Goal: Accurate, balanced, factual summary.
                """

        # Add product name if provided
        if product_name:
            prompt += f"Your task is to extract reviews for product {product_name}.\n"

        prompt += """Instructions:
                No need to extract product seller information.
                Extract Reviews & Key Info: Get all reviews. Note features, positives, negatives, context.
                Summarize Themes (No Overgeneralization): Find trends (praises, complaints). Quantify sentiment ("many," "few"). Avoid "everyone," "no one." Show mixed opinions if present.
                Accurate Sentiment (No Misrepresentation): Get overall tone (positive, negative, mixed). Use neutral language. Don't exaggerate.
                Relevant Info (No Irrelevance): Focus on common feedback, not single anecdotes.
                Factual Accuracy (No Hallucination): Stick to review text only. Verify facts. No made-up details.
                Provide Context: Explain why points matter if unclear.
                Appropriate Tone: Professional, neutral, clear language (no jargon/casual).
                Readable Length: Concise but comprehensive. Organized, not rambling.
                Bias & Fairness: Balanced view of positive/negative. No skewed portrayal.
                """

        # Add token limit instruction if specified
        if token_limit:
            prompt += f"\nToken Limit: Keep your response under {token_limit} tokens. Be more concise and prioritize important information while maintaining accuracy."

        prompt += "\nCurrent Input:\n" + article_text

        result = await agent.run(prompt)
        return result.data

    except Exception as e:
        logger.error(f"Failed to analyze review article: {str(e)}")
        raise


async def merge_reviews(
    review_texts: List[str], model_name: str, product_name: str, token_limit: Optional[int] = None, output_format: str = "structured"
) -> str:
    """
    Merge multiple review texts into a comprehensive product summary highlighting key features, pros, and cons.

    This function takes multiple review summaries (which could be from different sources or reviewers)
    and synthesizes them into a single, coherent product summary that helps users make purchase decisions.

    Args:
        review_texts: List of review text summaries to merge
        model_name: Name of the LLM to use for merging
        product_name: Name of the product being reviewed
        token_limit: Optional maximum token limit for the summary
        output_format: Format of the output summary - "structured" (with clear sections) or "narrative" (flowing text)

    Returns:
        A comprehensive product summary with key features, pros, and cons
    """
    try:
        logger.info(f"Merging {len(review_texts)} reviews for {product_name} using model: {model_name}")

        # Create appropriate model instance
        model = create_model(model_name)

        # Create agent with our result type
        agent = Agent(model=model, result_type=str)

        # Combine all review texts with separators
        combined_reviews = "\n\n===== REVIEW SEPARATOR =====\n\n".join(review_texts)

        # Base prompt for merging reviews
        prompt = f"""**Role**: Expert product analyst synthesizing multiple reviews for {product_name}.
        
Your task is to create a comprehensive summary that will help potential buyers make an informed purchase decision.

Instructions:
1. Analyze the multiple reviews provided below and identify key themes, patterns, and consensus points.
2. Create a well-structured summary that includes:
   - Product Overview: Brief description of what the product is and its key features
   - Key Features: The main characteristics and functionalities highlighted across reviews
   - Pros: The positive aspects consistently mentioned
   - Cons: The negative aspects or limitations consistently noted
   - Product comparison: How does this product compare to other products in the same category?
   - Verdict: A balanced conclusion about who should consider buying this product
3. For the formatting:
   - Use Short, Bold Headings
   - Use Bullet Points
   - Keep Sentences Short

Important guidelines:
- Maintain objectivity and present a balanced view
- Quantify opinions when possible (e.g., "most reviewers mentioned" vs. "one reviewer noted")
- Highlight both consensus and notable disagreements between reviewers
- Focus on helping users make purchase decisions, not just summarizing reviews
- Present information in a clear, organized manner
- Do not invent details not present in the reviews
- Prioritize information from genuine user experiences over marketing claims
"""

        # Add output format instruction
        if output_format == "structured":
            prompt += """
Format your response with clear section headers and bullet points for easy scanning.
Use a structure like:

# Product Overview
[Brief description]

## Key Features
- [Feature 1]
- [Feature 2]
...

## Pros
- [Pro 1]
- [Pro 2]
...

## Cons
- [Con 1]
- [Con 2]
...

## Verdict
[Balanced conclusion about who should consider buying]
"""
        elif output_format == "narrative":
            prompt += """
Format your response as a flowing narrative that's easy to read while still clearly highlighting the key features, pros, and cons.
"""

        # Add token limit instruction if specified
        if token_limit:
            prompt += f"\nToken Limit: Keep your response under {token_limit} tokens. Be concise while maintaining all critical information."

        prompt += "\n\nREVIEWS TO SYNTHESIZE:\n" + combined_reviews

        result = await agent.run(prompt)
        return result.data

    except Exception as e:
        logger.error(f"Failed to merge reviews: {str(e)}")
        raise


async def process_file(
    input_path: Path,
    output_dir: Optional[Path] = None,
    model_name: str = O3_MINI_MODEL,
    product_name: Optional[str] = None,
    token_limit: Optional[int] = None,
) -> Path:
    """Process a single review file.

    Args:
        input_path: Path to the input file to process
        output_dir: Directory to save output (uses input directory if None)
        model_name: Name of model to use
        product_name: Optional name of the product being reviewed
        token_limit: Optional token limit for the extraction

    Returns:
        Path to the output file
    """
    # Read input file
    with open(input_path, "r", encoding="utf-8") as f:
        article_text = f.read()

    # Run extraction
    analysis = await extract_reviews(article_text, model_name, product_name, token_limit)

    # Determine output path
    output_dir = output_dir or input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    model_suffix = model_name.replace("/", "-").lower()
    output_file = output_dir / f"{input_path.stem}.{model_suffix}.analysis.txt"

    # Save results
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(analysis)

    logger.success(f"Analysis for {input_path.name} saved to {output_file}")

    return output_file


async def process_batch(
    input_path: Path,
    output_dir: Optional[Path] = None,
    model_name: str = O3_MINI_MODEL,
    product_name: Optional[str] = None,
    token_limit: Optional[int] = None,
    file_pattern: str = "*.txt",
    show_progress: bool = True,
) -> List[Path]:
    """Process multiple review files in a batch.

    Args:
        input_path: Path to input directory or file
        output_dir: Directory to save outputs (uses input directory if None)
        model_name: Name of model to use
        product_name: Optional name of the product being reviewed
        token_limit: Optional token limit for the extraction
        file_pattern: Glob pattern for files to process (when input_path is a directory)
        show_progress: Whether to display a progress bar during processing

    Returns:
        List of paths to output files
    """
    # Check if input_path is a file or directory
    if input_path.is_file():
        # Process single file
        output_file = await process_file(input_path, output_dir, model_name, product_name, token_limit)
        return [output_file]
    elif input_path.is_dir():
        # Process directory of files
        output_dir = output_dir or input_path
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get list of files to process
        files = list(input_path.glob(file_pattern))

        if not files:
            logger.warning(f"No matching files found in {input_path} using pattern '{file_pattern}'")
            return []

        logger.info(f"Found {len(files)} files to process in {input_path}")

        # Process each file with optional progress tracking
        output_files = []

        if show_progress:
            for file in tqdm(files, desc="Processing files"):
                output_file = await process_file(file, output_dir, model_name, product_name, token_limit)
                output_files.append(output_file)
        else:
            for file in files:
                output_file = await process_file(file, output_dir, model_name, product_name, token_limit)
                output_files.append(output_file)

        return output_files
    else:
        logger.error(f"Input path {input_path} does not exist or is not accessible")
        return []


async def process_and_merge_files(
    input_path: Path,
    output_dir: Optional[Path] = None,
    model_name: str = O3_MINI_MODEL,
    product_name: str = None,
    token_limit: Optional[int] = None,
    file_pattern: str = "*.txt",
    merge_token_limit: Optional[int] = None,
    output_format: str = "structured",
    show_progress: bool = True,
) -> Path:
    """Process multiple review files and merge their extractions into a comprehensive product summary.

    This function first processes each review file individually and then combines all
    extracted reviews into a single, comprehensive product summary highlighting key
    features, pros, and cons to help users make purchase decisions.

    Args:
        input_path: Path to input directory or file
        output_dir: Directory to save outputs (uses input directory if None)
        model_name: Name of model to use
        product_name: Name of the product being reviewed (required)
        token_limit: Optional token limit for individual extractions
        file_pattern: Glob pattern for files to process (when input_path is a directory)
        merge_token_limit: Optional token limit for the merged summary
        output_format: Format of the merged summary ("structured" or "narrative")
        show_progress: Whether to display a progress bar during processing

    Returns:
        Path to the merged summary file
    """
    if not product_name:
        raise ValueError("Product name is required for merging reviews")

    # Process all individual review files
    logger.info(f"Processing review files for {product_name}")
    output_files = await process_batch(
        input_path=input_path,
        output_dir=output_dir,
        model_name=model_name,
        product_name=product_name,
        token_limit=token_limit,
        file_pattern=file_pattern,
        show_progress=show_progress,
    )

    if not output_files:
        logger.warning("No review files were processed, cannot generate merged summary")
        return None

    # Determine output directory
    output_dir = output_dir or (input_path if input_path.is_dir() else input_path.parent)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read all extracted reviews
    review_texts = []
    if show_progress:
        iterator = tqdm(output_files, desc="Reading extractions")
    else:
        iterator = output_files

    for file_path in iterator:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                review_texts.append(f.read())
        except Exception as e:
            logger.error(f"Failed to read extraction file {file_path}: {str(e)}")

    # Merge the reviews
    logger.info(f"Merging {len(review_texts)} extracted reviews into a comprehensive summary")
    merged_summary = await merge_reviews(
        review_texts=review_texts, model_name=model_name, product_name=product_name, token_limit=merge_token_limit, output_format=output_format
    )

    # Create a clean product name for the filename
    clean_product_name = "".join(c if c.isalnum() else "_" for c in product_name)
    clean_product_name = clean_product_name.strip("_")

    # Determine output file path
    model_suffix = model_name.replace("/", "-").lower()
    output_file = output_dir / f"{clean_product_name}_merged_summary.{model_suffix}.txt"

    # Save the merged summary
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(merged_summary)

    logger.success(f"Merged summary for {product_name} saved to {output_file}")
    return output_file


async def main():
    """Process a review article file and output structured analysis."""
    parser = argparse.ArgumentParser(description="Analyze and evaluate product review articles")
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")

    # Extract mode
    extract_parser = subparsers.add_parser("extract", help="Extract reviews from articles")
    extract_parser.add_argument("input_path", type=Path, help="Path to input file or directory")
    extract_parser.add_argument("--output-dir", "-o", type=Path, help="Directory to save outputs")
    extract_parser.add_argument("--model", "-m", default=O3_MINI_MODEL, help="Model to use for extraction")
    extract_parser.add_argument("--product-name", "-p", type=str, help="Name of the product being reviewed")
    extract_parser.add_argument("--token-limit", "-t", type=int, help="Maximum token limit for summaries")
    extract_parser.add_argument("--pattern", "--file-pattern", default="*.txt", help="File pattern when processing directories (default: *.txt)")

    # Merge mode
    merge_parser = subparsers.add_parser("merge", help="Process and merge multiple reviews into a comprehensive product summary")
    merge_parser.add_argument("input_path", type=Path, help="Path to input directory containing review files")
    merge_parser.add_argument("--output-dir", "-o", type=Path, help="Directory to save outputs")
    merge_parser.add_argument("--model", "-m", default=O3_MINI_MODEL, help="Model to use for extraction and merging")
    merge_parser.add_argument("--product-name", "-p", type=str, required=True, help="Name of the product being reviewed (required)")
    merge_parser.add_argument("--token-limit", "-t", type=int, help="Maximum token limit for individual extractions")
    merge_parser.add_argument("--merge-token-limit", type=int, help="Maximum token limit for the merged summary")
    merge_parser.add_argument("--pattern", "--file-pattern", default="*.txt", help="File pattern when processing directories (default: *.txt)")
    merge_parser.add_argument(
        "--output-format", choices=["structured", "narrative"], default="structured", help="Format of the merged summary (default: structured)"
    )

    # Evaluate mode
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate extraction quality")
    eval_parser.add_argument("raw_text_path", type=Path, help="Path to the original text file")
    eval_parser.add_argument("extraction_path", type=Path, help="Path to the extracted review text file")
    eval_parser.add_argument("--output", "-o", type=Path, help="Path to save evaluation results")
    eval_parser.add_argument("--model", "-m", default=O3_MINI_MODEL, help="Model to use for evaluation")

    # Backward compatibility with old CLI interface
    parser.add_argument("--eval", action="store_true", help="[DEPRECATED] Use 'evaluate' mode instead")
    parser.add_argument("--extraction-file", type=Path, help="[DEPRECATED] Use 'evaluate' mode instead")
    parser.add_argument("--output-file", type=Path, help="[DEPRECATED] Use 'evaluate' mode with --output")

    # Common options
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    try:
        # Configure logging
        logfire.configure(send_to_logfire="if-token-present", environment="dev", scrubbing=False)
        logfire.instrument_pydantic()
        logfire.instrument_httpx()

        # Set log level based on verbose flag
        if args.verbose:
            logger.level("INFO")
        else:
            logger.level("SUCCESS")

        # Process based on mode
        if args.mode == "extract":
            # Process batch of files or a single file
            output_files = await process_batch(args.input_path, args.output_dir, args.model, args.product_name, args.token_limit, args.pattern)

            print(f"\nProcessed {len(output_files)} files successfully.")

        elif args.mode == "merge":
            # Process and merge multiple reviews
            output_file = await process_and_merge_files(
                input_path=args.input_path,
                output_dir=args.output_dir,
                model_name=args.model,
                product_name=args.product_name,
                token_limit=args.token_limit,
                file_pattern=args.pattern,
                merge_token_limit=args.merge_token_limit,
                output_format=args.output_format,
            )

            if output_file:
                print(f"\nSuccessfully merged reviews into comprehensive summary: {output_file}")
            else:
                print("\nFailed to generate merged summary due to errors.")

        elif args.mode == "evaluate":
            # Validate input files
            if not args.raw_text_path.exists():
                logger.error(f"Error: File {args.raw_text_path} does not exist")
                sys.exit(1)

            if not args.extraction_path.exists():
                logger.error(f"Error: File {args.extraction_path} does not exist")
                sys.exit(1)

            # Run evaluation
            evaluation_results, output_path = await evaluate_extraction(args.raw_text_path, args.extraction_path, args.output, args.model)

            print("\nEvaluation Result:")
            print(json.dumps(evaluation_results, indent=2, ensure_ascii=False))
            logger.success(f"Evaluation saved to {output_path}")

        else:
            logger.error("Please specify a mode: extract, merge, or evaluate")
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        logger.error(
            f"Error processing file:\n" f"Error type: {type(e).__name__}\n" f"Error message: {str(e)}\n" f"Traceback:\n{traceback.format_exc()}"
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
