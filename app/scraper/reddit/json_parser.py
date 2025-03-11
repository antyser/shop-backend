"""Reddit JSON to markdown parser module."""

import json
from datetime import datetime
from typing import Any, Dict, List, TypedDict

from loguru import logger
from pydantic import BaseModel


class RedditComment(BaseModel):
    """Reddit comment model."""

    author: str
    body: str
    score: int
    created_utc: float
    replies: list["RedditComment"] = []


class RedditPost(BaseModel):
    """Reddit post model."""

    title: str
    author: str
    selftext: str
    score: int
    upvote_ratio: float
    created_utc: float
    num_comments: int
    url: str
    subreddit: str
    comments: list[RedditComment] = []


def format_timestamp(timestamp: float) -> str:
    """Format Unix timestamp to human readable date."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error formatting timestamp: {e}")
        return str(timestamp)


def format_comment(comment: RedditComment, depth: int = 0) -> str:
    """Format a comment and its replies recursively."""
    indent = "  " * depth
    lines = []

    # Format comment header
    lines.append(f"{indent}* **{comment.author}** ({comment.score} points) - {format_timestamp(comment.created_utc)}")

    # Format comment body with proper indentation
    body_lines = comment.body.strip().split("\n")
    for line in body_lines:
        lines.append(f"{indent}  {line}")

    # Add a blank line after the comment
    lines.append("")

    # Format replies recursively
    for reply in comment.replies:
        lines.append(format_comment(reply, depth + 1))

    return "\n".join(lines)


def parse_comment_data(data: dict[str, Any]) -> RedditComment | None:
    """Parse comment data from Reddit JSON."""
    try:
        if not isinstance(data, dict) or "kind" not in data or data["kind"] != "t1":
            return None

        comment_data = data["data"]
        comment = RedditComment(
            author=comment_data.get("author", "[deleted]"),
            body=comment_data.get("body", ""),
            score=comment_data.get("score", 0),
            created_utc=comment_data.get("created_utc", 0),
            replies=[],
        )

        # Parse replies recursively
        replies_data = comment_data.get("replies", {})
        if isinstance(replies_data, dict) and "data" in replies_data:
            for child in replies_data["data"].get("children", []):
                reply = parse_comment_data(child)
                if reply:
                    comment.replies.append(reply)

        return comment
    except Exception as e:
        logger.error(f"Error parsing comment data: {e}")
        return None


def parse_post_data(data: dict[str, Any]) -> RedditPost | None:
    """Parse post data from Reddit JSON."""
    try:
        if not isinstance(data, dict) or "kind" not in data or data["kind"] != "t3":
            return None

        post_data = data["data"]
        return RedditPost(
            title=post_data.get("title", ""),
            author=post_data.get("author", "[deleted]"),
            selftext=post_data.get("selftext", ""),
            score=post_data.get("score", 0),
            upvote_ratio=post_data.get("upvote_ratio", 0),
            created_utc=post_data.get("created_utc", 0),
            num_comments=post_data.get("num_comments", 0),
            url=post_data.get("url", ""),
            subreddit=post_data.get("subreddit", ""),
            comments=[],
        )
    except Exception as e:
        logger.error(f"Error parsing post data: {e}")
        return None


def extract_reddit_listing(json_data: Any) -> List[Dict[str, Any]]:
    """Extract Reddit listing data from various JSON structures."""
    # Handle Reddit's typical structure: [0] is post, [1] is comments
    if isinstance(json_data, list):
        result = []

        # If it's the standard Reddit API format with post and comments
        if len(json_data) >= 2 and all(isinstance(item, dict) and "data" in item for item in json_data[:2]):
            # Add the post if present
            if json_data[0].get("data", {}).get("children"):
                result.extend(json_data[0]["data"]["children"])
            # Add comments if present
            if json_data[1].get("data", {}).get("children"):
                result.extend(json_data[1]["data"]["children"])
            return result

        # If it's already a list of items
        return json_data

    if not isinstance(json_data, dict):
        return []

    # Handle single listing object
    if "data" in json_data and "children" in json_data["data"]:
        return json_data["data"]["children"]

    # Handle direct data object
    if "children" in json_data:
        return json_data["children"]

    return []


def process_comment_tree(comment_data: Dict[str, Any], depth: int = 0) -> List[str]:
    """Process a comment and its replies with proper indentation."""
    if not isinstance(comment_data, dict) or "data" not in comment_data:
        return []

    data = comment_data["data"]
    lines = []

    # Skip deleted/removed comments
    if data.get("author") in ["[deleted]", "[removed]"] and not data.get("body", "").strip():
        return []

    # Indentation prefix
    prefix = "  " * depth
    quote_prefix = "> " * (depth + 1) if depth > 0 else ""

    # Format comment header
    author = data.get("author", "[deleted]")
    score = data.get("score", 0)
    created = data.get("created_utc", 0)
    timestamp = format_timestamp(created)

    if depth == 0:
        lines.append(f"## Comment by u/{author}")
        lines.append(f"**Score: {score} | Posted: {timestamp}**\n")
    else:
        lines.append(f"{quote_prefix}**u/{author} | Score: {score}**")

    # Format comment body with proper indentation and remove links
    body = data.get("body", "").strip()
    if body:

        if depth == 0:
            # Top-level comments without quote formatting
            for line in body.split("\n"):
                lines.append(f"{prefix}{line}")
        else:
            # Nested comments with quote formatting
            for line in body.split("\n"):
                lines.append(f"{quote_prefix}{line}")

        lines.append("")  # Add a blank line after the comment

    # Process replies recursively
    replies = data.get("replies", {})
    if isinstance(replies, dict) and "data" in replies and "children" in replies["data"]:
        for child in replies["data"]["children"]:
            if child.get("kind") == "t1":  # Only process comments
                child_lines = process_comment_tree(child, depth + 1)
                lines.extend(child_lines)

    return lines


def convert_reddit_json_to_markdown(json_string: str) -> str:
    """
    Convert Reddit JSON response to markdown format

    Args:
        json_string: Raw JSON string from Reddit API

    Returns:
        Markdown formatted content
    """
    try:
        # Parse the JSON string into Python data structure
        if isinstance(json_string, str):
            json_data = json.loads(json_string)
        else:
            # Handle case where input is already parsed JSON
            json_data = json_string

        # Log the structure for debugging
        logger.debug(f"JSON structure type: {type(json_data)}")

        markdown_lines = []

        # Handle the standard Reddit API format (list with post and comments)
        if isinstance(json_data, list) and len(json_data) >= 2:
            # Extract post from first item
            post_data = None
            if isinstance(json_data[0], dict) and "data" in json_data[0] and "children" in json_data[0]["data"] and json_data[0]["data"]["children"]:
                post_item = json_data[0]["data"]["children"][0]
                if post_item.get("kind") == "t3" and "data" in post_item:
                    post_data = post_item["data"]

            # Format post content
            if post_data:
                title = post_data.get("title", "")
                author = post_data.get("author", "[deleted]")
                selftext = post_data.get("selftext", "")
                score = post_data.get("score", 0)
                upvote_ratio = post_data.get("upvote_ratio", 0.0)
                num_comments = post_data.get("num_comments", 0)
                created = post_data.get("created_utc", 0)

                markdown_lines.append(f"# {title}")
                markdown_lines.append(
                    f"**Posted by u/{author} | Score: {score} | "
                    f"Upvote Ratio: {upvote_ratio:.0%} | "
                    f"Comments: {num_comments} | "
                    f"Posted: {format_timestamp(created)}**\n"
                )


            # Extract and format comments
            if isinstance(json_data[1], dict) and "data" in json_data[1] and "children" in json_data[1]["data"]:
                comments = json_data[1]["data"]["children"]

                # Add a comments header if we have comments
                if comments:
                    markdown_lines.append("---")
                    markdown_lines.append("# Comments\n")

                for comment in comments:
                    if comment.get("kind") == "t1":  # Only process comments
                        comment_lines = process_comment_tree(comment)
                        markdown_lines.extend(comment_lines)

        if not markdown_lines:
            logger.warning("No Reddit content could be extracted")
            return "No Reddit content could be extracted"

        return "\n".join(markdown_lines)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Reddit JSON: {e}")
        return f"Error parsing Reddit JSON: {str(e)}"
    except Exception as e:
        logger.error(f"Error processing Reddit JSON: {e}", exc_info=True)
        return f"Error processing Reddit content: {str(e)}"


def fallback_reddit_parser(json_data: Any) -> str:
    """A simpler fallback parser for Reddit content."""
    try:
        markdown_lines = []

        # If it's the standard Reddit API format with post and comments
        if isinstance(json_data, list) and len(json_data) >= 2:
            # Extract post from first item
            if isinstance(json_data[0], dict) and "data" in json_data[0]:
                post_data = json_data[0]["data"]["children"][0]["data"] if json_data[0]["data"].get("children") else None
                if post_data:
                    title = post_data.get("title", "")
                    author = post_data.get("author", "[deleted]")
                    selftext = post_data.get("selftext", "")
                    score = post_data.get("score", 0)

                    markdown_lines.append(f"# {title}")
                    markdown_lines.append(f"**Posted by u/{author} | Score: {score}**\n")

                    if selftext:
                        markdown_lines.append(selftext + "\n")

            # Extract comments from second item
            if isinstance(json_data[1], dict) and "data" in json_data[1]:
                comments_data = json_data[1]["data"]["children"] if json_data[1]["data"].get("children") else []
                for comment_item in comments_data:
                    if "data" in comment_item:
                        comment_data = comment_item["data"]
                        author = comment_data.get("author", "[deleted]")
                        body = comment_data.get("body", "")
                        score = comment_data.get("score", 0)

                        if author and body:
                            markdown_lines.append(f"## Comment by u/{author}")
                            markdown_lines.append(f"**Score: {score}**\n")
                            markdown_lines.append(body + "\n")

                            # Process first-level replies
                            replies = comment_data.get("replies", {})
                            if isinstance(replies, dict) and "data" in replies:
                                reply_children = replies["data"].get("children", [])
                                for reply_item in reply_children:
                                    if "data" in reply_item:
                                        reply_data = reply_item["data"]
                                        reply_author = reply_data.get("author", "[deleted]")
                                        reply_body = reply_data.get("body", "")
                                        reply_score = reply_data.get("score", 0)

                                        if reply_author and reply_body:
                                            markdown_lines.append(f"> **u/{reply_author} | Score: {reply_score}**")
                                            markdown_lines.append(f"> {reply_body}\n")

        if not markdown_lines:
            return "Could not extract Reddit content with fallback parser"

        return "\n".join(markdown_lines)

    except Exception as e:
        logger.error(f"Fallback parser error: {e}", exc_info=True)
        return "Error in fallback Reddit parser"


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Test the parser with a sample JSON file
    if len(sys.argv) > 1:
        json_file = Path(sys.argv[1])
        if json_file.exists():
            try:
                json_string = json_file.read_text()
                markdown = convert_reddit_json_to_markdown(json_string)
                print(markdown)
            except Exception as e:
                logger.error(f"Error processing JSON file: {e}")
                sys.exit(1)
    else:
        logger.error("Please provide a JSON file path as argument")
        sys.exit(1)
