"""Models and functions for structured review analysis."""

import argparse
import json
import sys
import traceback
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import logfire
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.agents.constants import CLAUDE_SONNET_MODEL, O3_MINI_MODEL
from app.agents.model_factory import create_model
from app.config import get_settings


class Product(BaseModel):
    """A product mentioned in the review article."""

    name: str = Field(description="The name of the product")
    link: Optional[str] = Field(default=None, description="The link to the product")


class Review(BaseModel):
    """A review of a product."""

    products: List[Product] = Field(description="The products being reviewed")
    summary: str = Field(description="A summary of the review")


class ReviewExtraction(BaseModel):
    """Analysis of an article that may contain multiple product reviews."""

    reviews: List[Review] = Field(description="Analysis for each product mentioned")


def extract_reviews(article_text: str, model_name: str) -> ReviewExtraction:
    """
    Analyze a product review article and extract structured information.

    Args:
        article_text: The text content of the review article
        model_name: Name of the model to use for analysis

    Returns:
        ReviewArticleAnalysis object containing structured analysis of all products
        mentioned in the article
    """
    try:
        logger.info(f"Starting review article analysis using model: {model_name}")

        # Create appropriate model instance
        model = create_model(model_name)

        # Create agent with our result type
        agent = Agent(model=model, result_type=ReviewExtraction)

        # Run analysis
        prompt = (
            """**Role**: You're a master analyst extracting product reviews from raw text. 
                Track entities across the entire conversation and resolve ambiguous references.

                **Instructions**:
                1. Identify ALL products mentioned, even if referred to by pronouns later
                2. For EACH product:
                - Capture SPECIFIC ASPECTS discussed (performance, design, value, etc.)
                - Note both POSITIVE and NEGATIVE viewpoints
                - Record product links when explicitly provided
                3. Handle conversational context:
                - Maintain entity chain: "The speaker" → "they" → "it"
                - Cross-reference previous mentions when resolving pronouns
                4. Structure output EXACTLY as specified below
                5. If there's a clear separate review for a product, create a new review object for it.

                **Examples**:

                **Input**: 
                "I'm loving my new iPhone 15 (apple.com/iphone15). The camera is stellar, though I wish the battery lasted longer. They really nailed the design!"

                **Output**:
                {
                "reviews": [{
                    "products": [
                    {
                    "name": "iPhone 15",
                    "link": "apple.com/iphone15"
                    }
                    ],
                    "summary": "Positive review highlighting excellent camera and design, but notes shorter-than-desired battery life. Key aspects: camera quality, battery performance, design."
                }]
                }

                **Input**:
                Customer: "The ZFold5 feels fragile." 
                Support: "We recommend using their official case (samsung.com/galaxy-z-fold5-accessories)."
                Customer: "It helped, but it's still pricey."

                **Output**:
                {
                "reviews": [{
                    "products": [
                    {
                    "name": "ZFold5",
                    "link": "samsung.com/galaxy-z-fold5-accessories"
                    }
                    ],
                    "summary": "Mixed feedback - user expresses concerns about durability but acknowledges case helps. Criticizes high price. Key aspects: build quality, pricing, accessories."
                }]
                }

                **Current Input** (process EXACTLY per schema):
                
                """
            + article_text
        )

        result = agent.run_sync(prompt)
        return result.data

    except Exception as e:
        logger.error(f"Failed to analyze review article: {str(e)}")
        raise


class EvaluationScore(BaseModel):
    """Score and reasoning for a single evaluation aspect."""

    score: int = Field(ge=1, le=5, description="Score from 1-5")
    reason: str = Field(description="Detailed explanation for the score")


class ExtractionEvaluation(BaseModel):
    """Complete evaluation of review extraction quality."""

    accuracy: EvaluationScore
    coverage: EvaluationScore


def llm_evaluator(raw_text: str, extraction: ReviewExtraction, model_name: str = O3_MINI_MODEL) -> ExtractionEvaluation:
    """
    Evaluates the quality of review extraction using LLM-as-judge approach.

    Args:
        raw_text: Original text content
        extraction: Extracted review analysis
        model_name: Name of the model to use for evaluation

    Returns:
        ExtractionEvaluation with scores and reasons for accuracy and coverage
    """
    try:
        logger.info(f"Starting extraction evaluation using model: {model_name}")

        # Create appropriate model instance
        model = create_model(model_name)

        # Create agent with our result type
        agent = Agent(model=model, result_type=ExtractionEvaluation)

        evaluation_prompt = """Act as a quality assurance expert analyzing product review extraction results. Evaluate these aspects:

            1. **Accuracy** (1-5): How well do the extracted reviews match the source text?
            - 5: Perfect alignment with all facts, products, and sentiments
            - 3: Mostly correct but minor errors/missing details
            - 1: Major discrepancies or hallucinations

            2. **Coverage** (1-5): Are all products and key aspects captured?
            - 5: All products, features, and opinions included
            - 3: Missing some secondary aspects but main points covered
            - 1: Major omissions of products or key concepts

            Evaluation Steps:
            1. Compare extraction with original text
            2. Verify: 
            - Product names and links match mentions
            - All discussed features/aspects are in summaries
            - No introduced false information
            3. Identify missing elements or inaccuracies

            Format output as JSON with scores and specific reasons exactly like this:
            {{
              "accuracy": {{
                "score": 4,
                "reason": "Detailed explanation for accuracy score"
              }},
              "coverage": {{
                "score": 3,
                "reason": "Detailed explanation for coverage score"
              }}
            }}

            Now evaluate this case:

            Original Text:
            {text}

            Extraction Result:
            {result}

            Evaluation:"""

        # Format the extraction for LLM processing
        formatted_extraction = extraction.model_dump_json(indent=2)

        # Run evaluation using pydantic-ai agent
        try:
            result = agent.run_sync(evaluation_prompt.format(text=raw_text, result=formatted_extraction), model_settings={"temperature": 0.0})

            logger.success(f"Evaluation complete - Accuracy: {result.data.accuracy.score}/5, " f"Coverage: {result.data.coverage.score}/5")
            return result.data

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


def main():
    """Process a review article file and output structured analysis."""
    parser = argparse.ArgumentParser(description="Analyze and evaluate product review articles")
    parser.add_argument("input_file", type=Path, help="Path to the review article file")
    parser.add_argument("--model", default=O3_MINI_MODEL, help="Model to use for analysis")
    parser.add_argument("--eval", action="store_true", help="Evaluate an existing extraction file")
    parser.add_argument("--extraction-file", type=Path, help="Path to the extraction JSON file for evaluation")
    args = parser.parse_args()

    if not args.input_file.exists():
        logger.error(f"Error: File {args.input_file} does not exist")
        sys.exit(1)

    try:
        # Configure logging
        logfire.configure(send_to_logfire="if-token-present", environment="dev", scrubbing=False)
        logfire.instrument_pydantic()
        logfire.instrument_httpx()

        # Read the input file
        logger.info(f"Reading review from {args.input_file}")
        with open(args.input_file, "r", encoding="utf-8") as f:
            article_text = f.read()

        if args.eval:
            # Evaluation mode
            if not args.extraction_file:
                logger.error("Error: --extraction-file is required when using --eval")
                sys.exit(1)

            if not args.extraction_file.exists():
                logger.error(f"Error: Extraction file {args.extraction_file} does not exist")
                sys.exit(1)

            # Load the extraction file
            logger.info(f"Loading extraction from {args.extraction_file}")
            with open(args.extraction_file, "r", encoding="utf-8") as f:
                extraction_json = json.load(f)
                extraction = ReviewExtraction.model_validate(extraction_json)

            # Run evaluation
            evaluation = llm_evaluator(article_text, extraction, args.model)

            # Save evaluation results
            eval_file = args.extraction_file.with_suffix(".eval.json")
            evaluation_json = evaluation.model_dump(exclude_none=True)
            formatted_json = json.dumps(evaluation_json, indent=2, ensure_ascii=False)

            with open(eval_file, "w", encoding="utf-8") as f:
                f.write(formatted_json)

            logger.success(f"Evaluation saved to {eval_file}")
            print("\nEvaluation Result:")
            print(formatted_json)

        else:
            # Analysis mode
            analysis = extract_reviews(article_text, args.model)

            # Save analysis results
            model_suffix = args.model.replace("/", "-").lower()
            output_file = args.input_file.with_stem(f"{args.input_file.stem}.{model_suffix}").with_suffix(".analysis.json")

            analysis_json = analysis.model_dump(exclude_none=True)
            formatted_json = json.dumps(analysis_json, indent=2, ensure_ascii=False)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_json)

            logger.success(f"Analysis saved to {output_file}")
            print("\nAnalysis Result:")
            print(formatted_json)

    except Exception as e:
        logger.error(
            f"Error processing file:\n" f"Error type: {type(e).__name__}\n" f"Error message: {str(e)}\n" f"Traceback:\n{traceback.format_exc()}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
