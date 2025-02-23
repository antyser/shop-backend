"""Reddit JSON to markdown parser module."""

from datetime import datetime
from typing import Any, TypedDict

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


def convert_reddit_json_to_markdown(json_data: list[dict[str, Any]]) -> str:
    """Convert Reddit JSON data to markdown format."""
    try:
        if not isinstance(json_data, list) or len(json_data) < 2:
            raise ValueError("Invalid Reddit JSON data format")

        # Parse post data
        post_data = json_data[0]["data"]["children"][0]
        post = parse_post_data(post_data)
        if not post:
            raise ValueError("Failed to parse post data")

        # Parse comments
        comments_data = json_data[1]["data"]["children"]
        for comment_data in comments_data:
            comment = parse_comment_data(comment_data)
            if comment:
                post.comments.append(comment)

        # Format markdown
        lines = []

        # Post header
        lines.append(f"# {post.title}")
        lines.append("")
        lines.append(
            f"**Posted by u/{post.author}** ({post.score} points, {post.upvote_ratio*100:.0f}% upvoted) - {format_timestamp(post.created_utc)}"
        )
        lines.append("")

        # Post content
        if post.selftext:
            lines.append(post.selftext)
            lines.append("")

        # Post metadata
        lines.append("---")
        lines.append(f"**Subreddit**: r/{post.subreddit}")
        lines.append(f"**URL**: {post.url}")
        lines.append(f"**Comments**: {post.num_comments}")
        lines.append("---")
        lines.append("")

        # Comments
        if post.comments:
            lines.append("## Comments")
            lines.append("")
            for comment in post.comments:
                lines.append(format_comment(comment))

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error converting Reddit JSON to markdown: {e}")
        return f"Error: Failed to convert Reddit JSON to markdown - {str(e)}"


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    # Test the parser with a sample JSON file
    if len(sys.argv) > 1:
        json_file = Path(sys.argv[1])
        if json_file.exists():
            try:
                json_data = json.loads(json_file.read_text())
                markdown = convert_reddit_json_to_markdown(json_data)
                print(markdown)
            except Exception as e:
                logger.error(f"Error processing JSON file: {e}")
                sys.exit(1)
    else:
        logger.error("Please provide a JSON file path as argument")
        sys.exit(1)
