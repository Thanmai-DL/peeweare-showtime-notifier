import logging

from peeweare.exception import PeeweareException
from peeweare.models import CinemaMovieSession, MoviesShowing, Showtime
from peeweare.rest_adapter import RestAdapter


class PeeweareAPI:
    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        ssl_verify: bool = True,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the PeeweareAPI client.
        """
        self._rest_adapter = RestAdapter(url, headers, ssl_verify, logger)
        self._logger = logger or logging.getLogger(__name__)

    async def _showing(self, endpoint: str, key: str) -> list[MoviesShowing]:
        """
        Fetch the list of movies from the specified endpoint.

        Args:
            endpoint (str): The API endpoint to fetch movies from.
            key (str): The key to extract the movie list from the response.

        Returns:
            List[MoviesShowing]: The list of showing movies.
        """
        response = await self._rest_adapter.post(endpoint)
        try:
            data = response.data["output"][key]
        except Exception as e:
            self._logger.error(msg=str(e))
            raise PeeweareException(
                f"Error fetching movies from {endpoint}: {e}"
            ) from e
        return [MoviesShowing(**movie) for movie in data]

    async def _extract_dates(self, data: list[dict]) -> list:
        """
        Extract date values from the provided list of dictionaries into a list.

        Args:
            data (list[dict]): A list of dictionaries containing date information.

        Returns:
            list: A list of extracted dates.
        """
        return [item.get("dt") for item in data]

    async def nowshowing(self) -> list[MoviesShowing]:
        """
        Fetch the list of currently showing movies.

        Returns:
            List[MoviesShowing]: The list of currently showing movies.
        """
        return await self._showing("/nowshowing", "mv")

    async def comingsoon(self) -> list[MoviesShowing]:
        """
        Fetch the list of upcoming movies.

        Returns:
            List[MoviesShowing]: The list of upcoming movies.
        """
        return await self._showing("/comingsoon", "movies")

    async def all_movies(self) -> list[MoviesShowing]:
        """
        Fetch the list of all movies (currently showing and upcoming).

        Returns:
            List[MoviesShowing]: The combined list of currently showing and upcoming movies.
        """
        now_showing = await self.nowshowing()
        coming_soon = await self.comingsoon()
        return now_showing + coming_soon

    async def showtimes(
        self, movie_id: str, theater_id: str, date: str
    ) -> Showtime | None:
        """
        Fetch the showtimes for a specific movie at a specific theater on a given date.

        Args:
            movie_id (str): The ID of the movie.
            theater_id (str): The ID of the theater.
            date (str): The date for which to fetch showtimes (format: YYYY-MM-DD).

        Returns:
            Showtime | None: An object containing the showtimes for the specified movie, or None if the fetch fails.
        """

        self.movie_id = movie_id
        showtimes = Showtime(shows={})

        response = await self._rest_adapter.post("/csessions", {"cid": theater_id})
        if response.data["result"] == "success":
            if date in await self._extract_dates(response.data["output"]["days"]):
                try:
                    data = response.data["output"]["cinemaMovieSessions"]
                except TypeError:
                    self._logger.error(
                        msg=f"Showtime data for movie_id {movie_id} in theater_id {theater_id} on {date} is not available: 'output' or 'cinemaMovieSessions' key not found"
                    )
                    return None
                except Exception as e:
                    self._logger.error(msg=str(e))
                    raise PeeweareException(
                        f"Error fetching showtimes for movie_id {movie_id} in theater_id {theater_id} on {date}: {e}"
                    ) from e
                for session in data:
                    showtime = CinemaMovieSession(**session)
                    if str(showtime.movieRe.id) == movie_id:
                        for exp_session in showtime.experienceSessions:
                            showtimes.shows[exp_session.experience] = [
                                f"{show.showTime} ({show.language})"
                                for show in exp_session.shows
                            ]
                return showtimes
            else:
                self._logger.warning(
                    msg=f"Showtimes for movie_id {movie_id} in theater_id {theater_id} on {date} not updated yet"
                )
                return None
        else:
            raise PeeweareException(
                f"Failed to fetch showtimes for movie_id {movie_id} in theater_id {theater_id} on {date} due to API response: {response.data.get('result', 'Unknown error')} with message: {response.data.get('message', 'N/A')}"
            )
