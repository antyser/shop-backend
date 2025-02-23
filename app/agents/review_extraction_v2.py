"""Models and functions for structured review analysis."""

import argparse
import asyncio
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


async def extract_reviews(article_text: str, model_name: str) -> str:
    """
    Analyze a product review article and extract structured information.

    Args:
        article_text: The text content of the review article
        model_name: Name of the model to use for analysis

    Returns:
        A string containing the extracted review summary
    """
    try:
        logger.info(f"Starting review article analysis using model: {model_name}")

        # Create appropriate model instance
        model = create_model(model_name)

        # Create agent with our result type
        agent = Agent(model=model, result_type=str)

        # Run analysis
        prompt = (
            """**Role**: You're a master analyst extracting product reviews from raw text. 
                Extract the product reviews from the text.
                Write a summary of the reviews based on the information extracted in plain text(no markdown).
                
                Current Input:
                """
            + article_text
        )

        result = await agent.run(prompt)
        return result.data

    except Exception as e:
        logger.error(f"Failed to analyze review article: {str(e)}")
        raise


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


async def factuality_evaluator(raw_text: str, extraction: str, model_name: str, temperature: float = 0.0) -> ExtractionEvaluation:
    """Evaluates the quality of review extraction using sentence-by-sentence analysis.

    Args:
        raw_text: Original text content
        extraction: Extracted review text
        model_name: Name of the model to use for evaluation
        temperature: Temperature setting for model generation (default: 0.0)

    Returns:
        ExtractionEvaluation with sentence-by-sentence analysis
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
            result = await agent.run(evaluation_prompt.format(text=raw_text, response=extraction), model_settings={"temperature": temperature})

            logger.success(f"Evaluation complete - Analyzed {len(result.data.sentences)} sentences")
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


async def main():
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
                extraction_text = f.read()

            # Run evaluation
            evaluation = await factuality_evaluator(article_text, extraction_text, args.model)

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
            analysis = await extract_reviews(article_text, args.model)

            # Save analysis results
            model_suffix = args.model.replace("/", "-").lower()
            output_file = args.input_file.with_stem(f"{args.input_file.stem}.{model_suffix}").with_suffix(".analysis.txt")

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(analysis)

            logger.success(f"Analysis saved to {output_file}")
            print("\nAnalysis Result:")
            print(analysis)

    except Exception as e:
        logger.error(
            f"Error processing file:\n" f"Error type: {type(e).__name__}\n" f"Error message: {str(e)}\n" f"Traceback:\n{traceback.format_exc()}"
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
