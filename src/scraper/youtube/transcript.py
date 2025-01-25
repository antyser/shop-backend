from youtube_transcript_api import YouTubeTranscriptApi


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
        return _convert_transcript_to_text(transcript_list)
    except Exception:
        return None


async def aget_transcript(video_id: str) -> str | None:
    """Get YouTube video transcript as plain text.

    Args:
        video_id (str): YouTube video ID

    Returns:
        Optional[str]: Transcript text or None if not available
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return _convert_transcript_to_text(transcript_list)
    except Exception:
        return None


def get_transcripts(video_ids: list[str], continue_after_error: bool = True) -> tuple[dict[str, str | None], list[str]]:
    """Get transcripts for multiple YouTube videos.

    Args:
        video_ids (List[str]): List of YouTube video IDs
        continue_after_error (bool): Continue if error occurs

    Returns:
        Tuple[Dict[str, Optional[str]], List[str]]:
            - Dict mapping video IDs to transcripts
            - List of failed video IDs
    """
    transcripts, failed_ids = YouTubeTranscriptApi.get_transcripts(video_ids, languages=["en"], continue_after_error=continue_after_error)

    processed_transcripts = {video_id: _convert_transcript_to_text(transcript_list) for video_id, transcript_list in transcripts.items()}

    return processed_transcripts, failed_ids  # type: ignore
