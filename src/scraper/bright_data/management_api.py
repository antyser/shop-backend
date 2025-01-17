import httpx
from loguru import logger
from pydantic import BaseModel


class SnapshotStatus(BaseModel):
    """
    Bright Data snapshot status response

    Fields records, errors, and collection_duration
    are only present when status is 'ready'
    """

    status: str
    snapshot_id: str
    dataset_id: str
    records: int | None = None
    errors: int | None = None
    collection_duration: int | None = None


class SnapshotInfo(BaseModel):
    """Bright Data snapshot info response"""

    id: str | None = None
    dataset_id: str | None = None
    status: str | None = None
    dataset_size: int | None = None
    created: str | None = None


async def get_snapshot_status(snapshot_id: str, token: str) -> SnapshotStatus | None:
    """
    Get status of a specific snapshot

    Args:
        snapshot_id: ID of the snapshot to check
        token: Bright Data API token

    Returns:
        SnapshotStatus object or None if failed
    """
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}", headers=headers)
            response.raise_for_status()
            return SnapshotStatus(**response.json())

    except Exception as e:
        logger.error(f"Failed to get snapshot status: {str(e)}, response: {response.json()}")
        return None


async def list_snapshots(dataset_id: str, token: str, status: str = "ready") -> list[SnapshotInfo] | None:
    """
    List all snapshots for a dataset

    Args:
        dataset_id: ID of the dataset
        token: Bright Data API token
        status: Filter snapshots by status

    Returns:
        List of SnapshotInfo objects or None if failed
    """
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.brightdata.com/datasets/v3/snapshots" f"?dataset_id={dataset_id}&status={status}", headers=headers
            )
            response.raise_for_status()
            return [SnapshotInfo(**item) for item in response.json()]

    except Exception as e:
        logger.error(f"Failed to list snapshots: {str(e)}")
        return None
