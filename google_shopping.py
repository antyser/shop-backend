import os
import requests
from dotenv import load_dotenv
from loguru import logger

def search_google_shopping(
    query: str,
    location: str = "United States",
    gl: str = "us",
    hl: str = "en",
    page: int = 1
) -> dict:
    """
    Search Google Shopping using SearchAPI.io
    
    Args:
        query (str): Search query term
        location (str, optional): Location for search results. Defaults to "United States".
        gl (str, optional): Google location parameter. Defaults to "us".
        hl (str, optional): Interface language. Defaults to "en".
        page (int, optional): Results page number. Defaults to 1.
    
    Returns:
        dict: API response containing shopping results
    """
    # Load environment variables

    api_key = os.getenv("SEARCHAPI_API_KEY")
    
    # API endpoint
    url = "https://www.searchapi.io/api/v1/search"
    
    # Request parameters
    params = {
        "engine": "google_shopping",
        "q": query,
        "location": location,
        "gl": gl,
        "hl": hl,
        "page": page,
        "api_key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error calling SearchAPI: {str(e)}")

# Example usage
if __name__ == "__main__":
    load_dotenv()
    try:
        results = search_google_shopping("PS5", location="California,United States")
        logger.info(results)
    except Exception as e:
        logger.exception(f"Error: {e}")
