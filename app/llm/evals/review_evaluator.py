"""Evaluation functions for review extraction quality."""

import argparse
import asyncio
import json
import sys
import traceback
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import logfire
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from tqdm import tqdm

from app.llm.constants import CLAUDE_SONNET_MODEL, O3_MINI_MODEL
from app.llm.model_factory import create_model


class SentenceLabel(str, Enum):
    """Label for a sentence in the evaluation."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTORY = "contradictory"
    NO_RAD = "no_rad"


class SentenceEvaluation(BaseModel):
    """Evaluation of a single sentence."""

    sentence: str = Field(description="The sentence being analyzed")
    label: SentenceLabel = Field(description="The classification label for the sentence")
    rationale: str = Field(description="Brief explanation for the assigned label")
    excerpt: Optional[str] = Field(
        None,
        description="Relevant excerpt from context (required for supported/contradictory)",
    )


class ExtractionEvaluation(BaseModel):
    """Complete evaluation of review extraction quality."""

    sentences: List[SentenceEvaluation] = Field(description="Sentence-by-sentence analysis")


class CoverageLabel(str, Enum):
    """Label for aspect coverage in the evaluation."""

    COVERED = "covered"
    NOT_COVERED = "not_covered"


class AspectType(str, Enum):
    """Type of product aspect being evaluated."""

    PRODUCT_INFO = "product_info"
    USER_REVIEW = "user_review"


class AspectCoverage(BaseModel):
    """Evaluation of a single product aspect's coverage."""

    aspect_type: AspectType = Field(description="The type of product aspect being evaluated")
    aspect: str = Field(description="The product aspect being evaluated")
    label: CoverageLabel = Field(description="Whether the aspect is covered in the summary")
    rationale: str = Field(description="Brief explanation for the coverage assessment")


class CoverageEvaluation(BaseModel):
    """Complete evaluation of product aspect coverage."""

    product_name: str = Field(description="Name of the product being evaluated")
    aspects: List[AspectCoverage] = Field(description="Aspect-by-aspect coverage analysis")


async def coverage_evaluator(raw_text: str, summary: str, product_name: str, model_name: str, temperature: float = 1.0) -> Dict:
    """Evaluates if a summary covers all aspects of a product from the raw text.

    Args:
        raw_text: Original text content with product information
        summary: Extracted summary to evaluate
        product_name: Name of the product being reviewed
        model_name: Name of the model to use for evaluation
        temperature: Temperature setting for model generation (default: 1.0)

    Returns:
        Dictionary containing evaluation results with aspect-by-aspect coverage analysis
    """
    try:
        logger.info(f"Starting coverage evaluation for {product_name} using model: {model_name} (temp={temperature})")

        # Create appropriate model instance
        model = create_model(model_name)

        # Create agent with our result type
        agent = Agent(model=model, result_type=CoverageEvaluation)

        evaluation_prompt = """You are a meticulous product analyst. 
        Your task is to determine if a summary covers all the aspects about Product: {product_name} mentioned in the original text.

Instructions:
1. Identify all distinct aspects of the {product_name} mentioned in the original text (e.g., design, performance, price, usability, specific features). 
You should only include {product_name} aspects that are menteiond in the original text. If there's no {product_name} aspects in the original text, return an empty list.
2. Identify the type of aspect is from seller or customer:
   * **product_info**: The aspect is a product information from seller or manufacturer.
   * **user_review**: The aspect is a user review from customer.
3. Label each aspect as:
   * **covered**: The summary adequately addresses this aspect of the product.
   * **not_covered**: The summary fails to mention or inadequately addresses this aspect. Provide a brief rationale if is not covered, explaining your assessment.

Original Text:
{text}

Summary:
{summary}

Evaluation:"""

        # Run evaluation using pydantic-ai agent
        try:
            # Run the model
            result = await agent.run(
                evaluation_prompt.format(product_name=product_name, text=raw_text, summary=summary), model_settings={"temperature": temperature}
            )

            logger.success(f"Coverage evaluation complete - Analyzed {len(result.data.aspects)} aspects")

            # Convert Pydantic model to dictionary for plain text output
            return result.data.model_dump(exclude_none=True)

        except Exception as agent_error:
            logger.error(
                f"Agent run failed:\n"
                f"Error type: {type(agent_error).__name__}\n"
                f"Error message: {str(agent_error)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise

    except Exception as e:
        logger.error(
            f"Failed to evaluate coverage:\n" f"Error type: {type(e).__name__}\n" f"Error message: {str(e)}\n" f"Traceback:\n{traceback.format_exc()}"
        )
        raise


async def factuality_evaluator(raw_text: str, extraction: str, model_name: str, temperature: float = 1.0) -> Dict:
    """Evaluates the quality of review extraction using sentence-by-sentence analysis.

    Args:
        raw_text: Original text content
        extraction: Extracted review text
        model_name: Name of the model to use for evaluation
        temperature: Temperature setting for model generation (default: 1.0)

    Returns:
        Dictionary containing evaluation results with sentence-by-sentence analysis
    """
    try:
        logger.info(f"Starting extraction evaluation using model: {model_name} (temp={temperature})")

        # Create appropriate model instance
        model = create_model(model_name)

        # Create agent with our result type
        agent = Agent(model=model, result_type=ExtractionEvaluation)

        evaluation_prompt = """You are a helpful and harmless AI assistant. You will be provided with a textual context and a model-generated response. Your task is to analyze the response sentence by sentence and classify each sentence according to its relationship with the provided context.

Instructions:
1. Decompose the response into individual sentences.
2. For each sentence, assign one of the following labels:
* **supported**: The sentence is entailed by the given context. Provide a supporting excerpt from the context. The supporting except must fully entail the sentence. If you need to cite multiple supporting excepts, simply concatenate them.
* **unsupported**: The sentence is not entailed by the given context. No excerpt is needed for this label.
* **contradictory**: The sentence is falsified by the given context. Provide a contradicting excerpt from the context.
* **no_rad**: The sentence does not require factual attribution (e.g., opinions, greetings, questions, disclaimers). No excerpt is needed for this label.
3. For each label, provide a short rationale explaining your decision.
4. **Be very strict with your supported and contradictory decisions.** Unless you can find straightforward, indisputable evidence excerpts in the context that a sentence is supported or contradictory, consider it unsupported.
5. You should not employ world knowledge unless it is truly trivial.

Now evaluate this case:

Context:
{text}

Response:
{response}

Evaluation:"""

        # Run evaluation using pydantic-ai agent
        try:
            # Run the model without progress indicator
            result = await agent.run(evaluation_prompt.format(text=raw_text, response=extraction), model_settings={"temperature": temperature})

            logger.success(f"Evaluation complete - Analyzed {len(result.data.sentences)} sentences")

            # Convert Pydantic model to dictionary for plain text output
            return result.data.model_dump(exclude_none=True)

        except Exception as agent_error:
            logger.error(
                f"Agent run failed:\n"
                f"Error type: {type(agent_error).__name__}\n"
                f"Error message: {str(agent_error)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise

    except Exception as e:
        logger.error(
            f"Failed to evaluate extraction:\n"
            f"Error type: {type(e).__name__}\n"
            f"Error message: {str(e)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )
        raise


async def evaluate_extraction(
    raw_text_path: Union[Path, str],
    extraction_path: Union[Path, str],
    output_path: Optional[Path] = None,
    model_name: str = O3_MINI_MODEL,
    evaluation_type: str = "factuality",
    product_name: Optional[str] = None,
) -> Tuple[Dict, Path]:
    """Evaluate review extraction quality.

    Args:
        raw_text_path: Path to the original text file
        extraction_path: Path to the extracted review text file
        output_path: Path to save evaluation results (optional)
        model_name: Name of the model to use for evaluation
        evaluation_type: Type of evaluation to perform ("factuality" or "coverage")
        product_name: Name of the product (required for coverage evaluation)

    Returns:
        Tuple containing:
            - Dictionary with evaluation results
            - Path where the evaluation results were saved
    """
    # Convert to Path objects if strings
    raw_text_path = Path(raw_text_path) if isinstance(raw_text_path, str) else raw_text_path
    extraction_path = Path(extraction_path) if isinstance(extraction_path, str) else extraction_path

    # Read input files
    with open(raw_text_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    with open(extraction_path, "r", encoding="utf-8") as f:
        extraction_text = f.read()

    # Run appropriate evaluation
    if evaluation_type == "factuality":
        evaluation_results = await factuality_evaluator(raw_text, extraction_text, model_name)
        eval_suffix = ".fact-eval.json"
    elif evaluation_type == "coverage":
        if not product_name:
            raise ValueError("Product name is required for coverage evaluation")
        evaluation_results = await coverage_evaluator(raw_text, extraction_text, product_name, model_name)
        eval_suffix = ".cov-eval.json"
    else:
        raise ValueError(f"Unknown evaluation type: {evaluation_type}")

    # Determine output path if not provided
    if not output_path:
        output_path = extraction_path.with_suffix(eval_suffix)

    # Save evaluation results as JSON
    formatted_json = json.dumps(evaluation_results, indent=2, ensure_ascii=False)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(formatted_json)

    logger.success(f"Evaluation saved to {output_path}")

    return evaluation_results, output_path


async def main():
    """Run review evaluation from the command line."""
    parser = argparse.ArgumentParser(description="Evaluate review article extractions")

    # Create subparsers for different evaluation types
    subparsers = parser.add_subparsers(dest="eval_type", required=True, help="Type of evaluation to perform")

    # Factuality evaluation subcommand
    fact_parser = subparsers.add_parser("factuality", help="Evaluate factual accuracy of extractions")
    fact_parser.add_argument("directory", type=Path, help="Directory containing both raw text and extraction files")
    fact_parser.add_argument("--raw-suffix", default=".txt", help="Suffix for raw text files")
    fact_parser.add_argument("--extraction-suffix", default=".analysis.txt", help="Suffix for extraction files")
    fact_parser.add_argument("--output-suffix", default=".fact-eval.json", help="Suffix for output files")
    fact_parser.add_argument("--model", "-m", default=O3_MINI_MODEL, help="Model to use for evaluation")

    # Coverage evaluation subcommand
    cov_parser = subparsers.add_parser("coverage", help="Evaluate aspect coverage of extractions")
    cov_parser.add_argument("directory", type=Path, help="Directory containing both raw text and extraction files")
    cov_parser.add_argument("--product-name", "-p", help="Name of the product being reviewed (required)")
    cov_parser.add_argument("--raw-suffix", default=".txt", help="Suffix for raw text files")
    cov_parser.add_argument("--extraction-suffix", default=".analysis.txt", help="Suffix for extraction files")
    cov_parser.add_argument("--output-suffix", default=".cov-eval.json", help="Suffix for output files")
    cov_parser.add_argument("--model", "-m", default=O3_MINI_MODEL, help="Model to use for evaluation")
    cov_parser.add_argument("--product-names", type=Path, help="JSON file mapping filenames to product names")

    # Common options
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")

    args = parser.parse_args()

    # Configure logging
    logfire.configure(send_to_logfire="if-token-present", environment="dev", scrubbing=False)
    logfire.instrument_pydantic()

    # Set log level based on verbose flag
    if args.verbose:
        logger.level("INFO")
    else:
        logger.level("SUCCESS")

    try:
        # Validate directory
        if not args.directory.exists() or not args.directory.is_dir():
            logger.error(f"Directory does not exist: {args.directory}")
            return 1

        # Find extraction files
        extraction_files = list(args.directory.glob(f"*{args.extraction_suffix}"))

        if not extraction_files:
            logger.error(f"No extraction files found in {args.directory} with suffix '{args.extraction_suffix}'")
            return 1

        logger.info(f"Found {len(extraction_files)} extraction files to evaluate")

        # Load product names if provided (for coverage evaluation)
        product_names = {}
        if args.eval_type == "coverage" and args.product_names and args.product_names.exists():
            with open(args.product_names, "r", encoding="utf-8") as f:
                product_names = json.load(f)
            logger.info(f"Loaded {len(product_names)} product names from {args.product_names}")

        # Process each file
        results = []

        iterator = tqdm(extraction_files, desc="Evaluating files") if not args.no_progress else extraction_files

        for extraction_file in iterator:
            # Get base name without extraction suffix
            base_name = extraction_file.name
            if base_name.endswith(args.extraction_suffix):
                base_name = base_name[: -len(args.extraction_suffix)]

            # Find corresponding raw text file
            raw_file = args.directory / f"{base_name}{args.raw_suffix}"

            if not raw_file.exists():
                logger.warning(f"Could not find raw text file for {extraction_file.name}")
                continue

            # Determine output path
            output_file = args.directory / f"{base_name}{args.output_suffix}"

            if args.eval_type == "factuality":
                # Run factuality evaluation
                try:
                    evaluation_results, _ = await evaluate_extraction(
                        raw_text_path=raw_file,
                        extraction_path=extraction_file,
                        output_path=output_file,
                        model_name=args.model,
                        evaluation_type="factuality",
                    )
                    results.append(evaluation_results)
                except Exception as e:
                    logger.error(f"Factuality evaluation failed for {extraction_file.name}: {str(e)}")

            elif args.eval_type == "coverage":
                # Get product name
                product_name = None
                if base_name in product_names:
                    product_name = product_names[base_name]
                elif args.product_name:
                    product_name = args.product_name
                else:
                    logger.error(f"No product name provided for {extraction_file.name}")
                    continue

                # Run coverage evaluation
                try:
                    evaluation_results, _ = await evaluate_extraction(
                        raw_text_path=raw_file,
                        extraction_path=extraction_file,
                        output_path=output_file,
                        model_name=args.model,
                        evaluation_type="coverage",
                        product_name=product_name,
                    )
                    results.append(evaluation_results)
                except Exception as e:
                    logger.error(f"Coverage evaluation failed for {extraction_file.name}: {str(e)}")

        # Print summary
        print(f"\nEvaluation completed for {len(results)} files")

        if args.eval_type == "coverage" and results:
            # Aggregate coverage statistics
            total_aspects = 0
            covered_aspects = 0
            product_info_aspects = 0
            user_review_aspects = 0

            # New counters for detailed statistics
            product_info_covered = 0
            product_info_not_covered = 0
            user_review_covered = 0
            user_review_not_covered = 0

            for result in results:
                aspects = result.get("aspects", [])
                total_aspects += len(aspects)

                for aspect in aspects:
                    is_covered = aspect.get("label") == "covered"
                    aspect_type = aspect.get("aspect_type")

                    if is_covered:
                        covered_aspects += 1

                    if aspect_type == "product_info":
                        product_info_aspects += 1
                        if is_covered:
                            product_info_covered += 1
                        else:
                            product_info_not_covered += 1
                    elif aspect_type == "user_review":
                        user_review_aspects += 1
                        if is_covered:
                            user_review_covered += 1
                        else:
                            user_review_not_covered += 1

            print("\nAggregate Coverage Statistics:")
            print(f"Total aspects analyzed: {total_aspects}")

            if total_aspects > 0:
                covered_pct = (covered_aspects / total_aspects) * 100
                not_covered_pct = 100 - covered_pct
                product_info_pct = (product_info_aspects / total_aspects) * 100
                user_review_pct = (user_review_aspects / total_aspects) * 100

                print(f"Covered: {covered_aspects} ({covered_pct:.1f}%)")
                print(f"Not covered: {total_aspects - covered_aspects} ({not_covered_pct:.1f}%)")
                print(f"Product info aspects: {product_info_aspects} ({product_info_pct:.1f}%)")
                print(f"User review aspects: {user_review_aspects} ({user_review_pct:.1f}%)")

                # New detailed statistics by aspect type
                print("\nDetailed Coverage by Aspect Type:")

                # Product info stats
                if product_info_aspects > 0:
                    product_info_covered_pct = (product_info_covered / product_info_aspects) * 100
                    product_info_not_covered_pct = 100 - product_info_covered_pct
                    print(f"Product info covered: {product_info_covered} ({product_info_covered_pct:.1f}%)")
                    print(f"Product info not covered: {product_info_not_covered} ({product_info_not_covered_pct:.1f}%)")
                else:
                    print("No product info aspects found")

                # User review stats
                if user_review_aspects > 0:
                    user_review_covered_pct = (user_review_covered / user_review_aspects) * 100
                    user_review_not_covered_pct = 100 - user_review_covered_pct
                    print(f"User review covered: {user_review_covered} ({user_review_covered_pct:.1f}%)")
                    print(f"User review not covered: {user_review_not_covered} ({user_review_not_covered_pct:.1f}%)")
                else:
                    print("No user review aspects found")

        elif args.eval_type == "factuality" and results:
            # Aggregate factuality statistics
            total_sentences = 0
            supported_sentences = 0
            unsupported_sentences = 0
            contradictory_sentences = 0
            no_rad_sentences = 0

            for result in results:
                sentences = result.get("sentences", [])
                total_sentences += len(sentences)

                for sentence in sentences:
                    label = sentence.get("label")
                    if label == "supported":
                        supported_sentences += 1
                    elif label == "unsupported":
                        unsupported_sentences += 1
                    elif label == "contradictory":
                        contradictory_sentences += 1
                    elif label == "no_rad":
                        no_rad_sentences += 1

            print("\nAggregate Factuality Statistics:")
            print(f"Total sentences analyzed: {total_sentences}")

            if total_sentences > 0:
                supported_pct = (supported_sentences / total_sentences) * 100
                unsupported_pct = (unsupported_sentences / total_sentences) * 100
                contradictory_pct = (contradictory_sentences / total_sentences) * 100
                no_rad_pct = (no_rad_sentences / total_sentences) * 100

                print(f"Supported: {supported_sentences} ({supported_pct:.1f}%)")
                print(f"Unsupported: {unsupported_sentences} ({unsupported_pct:.1f}%)")
                print(f"Contradictory: {contradictory_sentences} ({contradictory_pct:.1f}%)")
                print(f"No RAD: {no_rad_sentences} ({no_rad_pct:.1f}%)")

        return 0

    except Exception as e:
        logger.error(f"Error: {str(e)}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
