from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi

from app.utils.counter import crawler_counter


def _convert_transcript_to_text(transcript_list: list[dict]) -> str:
    """Convert transcript list to formatted text with periods.

    Args:
        transcript_list (List[Dict]): Raw transcript data

    Returns:
        str: Formatted transcript text with proper periods
    """
    transcript_text = ". ".join(entry["text"].strip() for entry in transcript_list)
    if not transcript_text.endswith("."):
        transcript_text += "."
    return transcript_text


def get_transcript(video_id: str) -> str | None:
    """Get YouTube video transcript as plain text.

    Args:
        video_id (str): YouTube video ID

    Returns:
        Optional[str]: Transcript text or None if not available
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        text = _convert_transcript_to_text(transcript_list)
        crawler_counter.add(1, {"type": "youtube", "status": "success"})
        return text
    except Exception as e:
        logger.error(f"Failed to get transcript for video {video_id}: {e}")
        crawler_counter.add(1, {"type": "youtube", "status": "error", "error": "transcript"})
        return None


async def aget_transcript(video_id: str) -> str | None:
    """Get YouTube video transcript as plain text.

    Args:
        video_id (str): YouTube video ID

    Returns:
        Optional[str]: Transcript text or None if not available
    """
    try:
        logger.info(f"Getting transcript for video {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        text = _convert_transcript_to_text(transcript_list)
        crawler_counter.add(1, {"type": "youtube", "status": "success"})
        return text
    except Exception as e:
        logger.error(f"Failed to get transcript for video {video_id}: {e}")
        crawler_counter.add(1, {"type": "youtube", "status": "error", "error": "transcript"})
        return None
