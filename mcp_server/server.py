import logging

from httpx2 import AsyncClient, HTTPStatusError, Response
from mcp.server import MCPServer

# Logging configuration
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize MCPServer
mcp = MCPServer("Peeweare Showtime Notifier MCP")

# Constants
PSN_API_BASE = "http://127.0.0.1:8000"
USER_AGENT = "peeweare_showtime_notifier/1.0"


# Helper function
async def make_request(method: str, url: str, payload: dict | None = None) -> Response:
    """
    Make an HTTP request to the specified URL with the given method and payload.

    Args:
        method (str): The HTTP method to use.
        url (str): The URL to send the request to.
        payload (dict | None): The data to send in the request.

    Returns:
        Response: The response from the request.
    """
    async with AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers={"User-Agent": USER_AGENT},
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            return response
        except HTTPStatusError as e:
            logger.error(f"HTTP error occurred while fetching data from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None


# Tools
@mcp.tool()
async def fetch_movies(category: str) -> list[dict] | None:
    """
    Fetch the list of movies from the specified category.

    Args:
        category (str): The category of movies to fetch between "nowshowing" and "comingsoon".

    Returns:
        list[dict]: The list of movies in the specified category.
    """
    url = f"{PSN_API_BASE}/movies/lists/{category}"
    response = await make_request("GET", url)
    if response is None:
        logger.error(
            f"Unable to fetch {category} movies from Peeweare API. Status code: {response.status_code if response else 'N/A'}"
        )
        return f"Unable to fetch {category} movies from Peeweare API."
    elif response.json() == []:
        logger.info(f"No {category} movies found.")
        return f"No {category} movies found."
    return response.json()


@mcp.tool()
async def create_monitoring_job(
    movie_id: str, name: str, theater_id: str, date: str, imax: bool
) -> str:
    """
    Create a monitoring job for a specific movie.

    Args:
        movie_id (str): The ID of the movie to monitor.
        name (str): The name of the movie.
        theater_id (str): The ID of the theater to monitor.
        date (str): The date to monitor the movie in YYYY-MM-DDTHH:MM:SS+05:30 format.
        imax (bool): Whether to monitor IMAX showtimes.

    Returns:
        str: A message indicating the result of the job creation.
    """
    url = f"{PSN_API_BASE}/movies/monitoring/create"
    payload = {
        "movie_id": movie_id,
        "name": name,
        "theater_id": theater_id,
        "release_date": date,
        "imax": imax,
    }
    response = await make_request("POST", url, payload)
    if response is None:
        logger.error(
            f"Unable to create monitoring job for {name}. Status code: {response.status_code if response else 'N/A'}"
        )
        return f"Unable to create monitoring job for {name}. Status code: {response.status_code if response else 'N/A'}"
    elif response.status_code != 201:
        logger.error(
            f"Failed to create monitoring job for {name}. Status code: {response.status_code if response else 'N/A'}. Response : {response.json() if response else 'N/A'}"
        )
        return f"Failed to create monitoring job for {name}. Status code: {response.status_code if response else 'N/A'}. Response: {response.json() if response else 'N/A'}"
    return f"Monitoring job created for {name}. Status code: {response.status_code}. Response: {response.json()}"


@mcp.tool()
async def list_monitoring_jobs() -> list[dict] | str:
    """
    List all active monitoring jobs.

    Returns:
        list[dict]: A list of active monitoring jobs.
    """
    url = f"{PSN_API_BASE}/movies/monitoring/list"
    response = await make_request("GET", url)
    if response is None:
        logger.error(
            f"Unable to fetch monitoring jobs from Peeweare API. Status code: {response.status_code if response else 'N/A'}"
        )
        return f"Unable to fetch monitoring jobs from Peeweare API. Status code: {response.status_code if response else 'N/A'}"
    elif response.json() == []:
        logger.info("No active monitoring jobs found.")
        return "No active monitoring jobs found."
    return response.json()


@mcp.tool()
async def delete_monitoring_job(movie_id: str) -> str:
    """
    Delete a monitoring job by its movie ID.

    Args:
        movie_id (str): The ID of the movie for which to delete monitoring job.

    Returns:
        str: A message indicating the result of the deletion.
    """
    url = f"{PSN_API_BASE}/movies/monitoring/delete?movie_id={movie_id}"
    response = await make_request("DELETE", url)
    if response is None:
        return f"Unable to delete monitoring job with ID {movie_id}. Status code: {response.status_code if response else 'N/A'}"
    elif response.status_code != 204:
        return f"Failed to delete monitoring job with ID {movie_id}. Status code: {response.status_code if response else 'N/A'}. Response: {response.json() if response else 'N/A'}"
    return f"Monitoring job with ID {movie_id} deleted successfully."


# Resouces
@mcp.resource("ids://theaterids", mime_type="application/json")
def get_theater_ids() -> dict:
    """
    Get the list of theater IDs.

    Returns:
        list[dict]: A list of theater IDs.
    """
    return {
        "PVR GLOBAL MALL": "534",
        "PVR GT WORLD MALL": "519",
        "PVR SUPERPLEX FORUM MALL": "533",
        "PVR ORION MALL": "511",
        "PVR VAISHNAVI SAPPHIRE MALL": "391",
        "INOX MANTRI SQUARE": "148",
        "INOX SHREE GARUDA SWAGATH MALL": "127",
        "INOX CENTRAL": "150",
        "PVR VEGA CITY": "520",
        "PVR NEXUS": "507",
        "PVR DIRECTORS CUT FORUM REX WALK": "529",
        "INOX GARUDA MALL": "110",
        "INOX LIDO MALL": "14",
        "INOX MEGAPLEX MALL OF ASIA": "309",
        "INOX GARUDA YELAHANKA": "261",
        "PVR MSR ELEMENTS MALL": "385",
        "INOX GALLERIA MALL": "231",
        "PVR CENTRAL SPIRIT MALL": "510",
        "INOX M5 ECITY": "583",
        "PVR BHARTIYA MALL OF BENGALURU": "531",
        "PVR VR BENGALURU": "390",
        "PVR PHOENIX MARKETCITY MALL": "512",
        "INOX BROOKEFIELD MALL": "208",
        "PVR AURA PARK SQUARE WHITEFIELD": "522",
        "INOX NEXUS WHITEFIELD": "24",
        "INOX SBR HORIZON": "282",
        "PVR ORION UPTOWN": "528",
    }
