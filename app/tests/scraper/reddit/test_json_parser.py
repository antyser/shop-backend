"""Tests for Reddit JSON parser."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from app.scraper.reddit.json_parser import (
    RedditComment,
    RedditPost,
    convert_reddit_json_to_markdown,
    format_comment,
    format_timestamp,
    parse_comment_data,
    parse_post_data,
)

# Sample test data
SAMPLE_POST_DATA = {
    "kind": "t3",
    "data": {
        "title": "Test Post",
        "author": "test_user",
        "selftext": "This is a test post",
        "score": 100,
        "upvote_ratio": 0.95,
        "created_utc": 1612345678,
        "num_comments": 2,
        "url": "https://reddit.com/r/test/comments/123/test_post",
        "subreddit": "test",
    },
}

SAMPLE_COMMENT_DATA = {
    "kind": "t1",
    "data": {
        "author": "commenter",
        "body": "Test comment",
        "score": 50,
        "created_utc": 1612345679,
        "replies": {
            "data": {
                "children": [
                    {
                        "kind": "t1",
                        "data": {
                            "author": "replier",
                            "body": "Test reply",
                            "score": 25,
                            "created_utc": 1612345680,
                            "replies": "",
                        },
                    }
                ]
            }
        },
    },
}

SAMPLE_REDDIT_JSON = [
    {"data": {"children": [SAMPLE_POST_DATA]}},
    {"data": {"children": [SAMPLE_COMMENT_DATA]}},
]


def test_format_timestamp():
    """Test timestamp formatting."""
    timestamp = 1612345678
    expected = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    assert format_timestamp(timestamp) == expected


def test_format_comment():
    """Test comment formatting."""
    comment = RedditComment(
        author="test_user",
        body="Test comment\nwith multiple lines",
        score=10,
        created_utc=1612345678,
    )
    markdown = format_comment(comment)
    assert "**test_user**" in markdown
    assert "(10 points)" in markdown
    assert "Test comment" in markdown
    assert "with multiple lines" in markdown


def test_parse_comment_data():
    """Test comment data parsing."""
    comment = parse_comment_data(SAMPLE_COMMENT_DATA)
    assert comment is not None
    assert comment.author == "commenter"
    assert comment.body == "Test comment"
    assert comment.score == 50
    assert len(comment.replies) == 1
    assert comment.replies[0].author == "replier"


def test_parse_post_data():
    """Test post data parsing."""
    post = parse_post_data(SAMPLE_POST_DATA)
    assert post is not None
    assert post.title == "Test Post"
    assert post.author == "test_user"
    assert post.selftext == "This is a test post"
    assert post.score == 100
    assert post.upvote_ratio == 0.95
    assert post.num_comments == 2
    assert post.subreddit == "test"


def test_convert_reddit_json_to_markdown():
    """Test full JSON to markdown conversion."""
    markdown = convert_reddit_json_to_markdown(SAMPLE_REDDIT_JSON)
    assert "# Test Post" in markdown
    assert "**Posted by u/test_user**" in markdown
    assert "This is a test post" in markdown
    assert "**Subreddit**: r/test" in markdown
    assert "## Comments" in markdown
    assert "**commenter**" in markdown
    assert "**replier**" in markdown


def test_invalid_json_data():
    """Test handling of invalid JSON data."""
    invalid_data = [{"data": {}}]  # Missing required data
    markdown = convert_reddit_json_to_markdown(invalid_data)
    assert "Error:" in markdown


def test_missing_fields():
    """Test handling of missing fields."""
    incomplete_post = {
        "kind": "t3",
        "data": {
            "title": "Test Post",
            # Missing other fields
        },
    }
    post = parse_post_data(incomplete_post)
    assert post is not None
    assert post.title == "Test Post"
    assert post.author == "[deleted]"  # Default value
    assert post.score == 0  # Default value


def test_real_reddit_json():
    """Test with real Reddit JSON data."""
    json_file = Path.home() / "Downloads" / "how_do_we_feel_about_paulas_choice_antiaging.json"
    if not json_file.exists():
        pytest.skip("Reddit JSON file not found")

    with json_file.open() as f:
        json_data = json.load(f)

    markdown = convert_reddit_json_to_markdown(json_data)
    assert markdown is not None
    assert not markdown.startswith("Error:")
    assert "# " in markdown  # Should have a title
    assert "**Posted by" in markdown  # Should have author info
    assert "**Subreddit**: r/" in markdown  # Should have subreddit info


if __name__ == "__main__":
    pytest.main([__file__])
