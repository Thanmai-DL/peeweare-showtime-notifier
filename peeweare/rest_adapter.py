import logging
from json import JSONDecodeError

import httpx

from peeweare.exception import PeeweareException
from peeweare.models import Result


class RestAdapter:
    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        ssl_verify: bool = True,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the API client.

        Args:
            url (str): The base URL for the API.
            headers (Dict[str, str]): The headers for the API requests.
            ssl_verify (bool): Whether to verify SSL certificates.
            logger (logging.Logger): The logger to use.
        """
        self.base_url = url
        self._headers = headers or {}
        self._ssl_verify = ssl_verify
        self._logger = logger or logging.getLogger(__name__)

    async def _do(
        self, method: str, endpoint: str, json_data: dict[str, str] | None = None
    ) -> Result:
        """
        Perform a request to the API.

        Args:
            method (str): The HTTP method.
            endpoint (str): The API endpoint.
            json_data (Dict[str, str], optional): The JSON data for the request.

        Returns:
            Result: The result of the API request.
        """
        http_method = method.upper()
        url = self.base_url + endpoint
        headers = self._headers

        log_line_pre = f"method={http_method}, url={url}"
        log_line_post = f"{log_line_pre}, success={{}}, status_code={{}}, message={{}}"

        try:
            self._logger.debug(msg=log_line_pre)
            async with httpx.AsyncClient(verify=self._ssl_verify) as client:
                response = await client.request(
                    method=http_method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    timeout=None,
                )
        except httpx.HTTPError as e:
            self._logger.error(msg=str(e))
            raise PeeweareException("Request failed") from e
        try:
            data_out = response.json()
        except (ValueError, JSONDecodeError) as e:
            self._logger.error(msg=log_line_post.format(False, response.status_code, e))
            raise PeeweareException("Bad JSON response") from e
        is_success = 299 >= response.status_code >= 200
        log_line = log_line_post.format(
            is_success, response.status_code, response.reason_phrase
        )
        if is_success:
            self._logger.debug(msg=log_line)
            return Result(
                status_code=response.status_code,
                message=response.reason_phrase,
                data=data_out,
            )
        self._logger.error(msg=log_line)
        raise PeeweareException(
            f"Request failed with status code {response.status_code}: {response.reason_phrase}"
        )

    async def get(
        self, endpoint: str, json_data: dict[str, str] | None = None
    ) -> Result:
        """
        Perform a GET request to the API.

        Args:
            endpoint (str): The API endpoint.
            json_data (Dict[str, str], optional): The JSON data for the request.

        Returns:
            Result: The result of the API request.
        """
        return await self._do("GET", endpoint=endpoint, json_data=json_data)

    async def post(
        self, endpoint: str, json_data: dict[str, str] | None = None
    ) -> Result:
        """
        Perform a POST request to the API.

        Args:
            endpoint (str): The API endpoint.
            json_data (Dict[str, str], optional): The JSON data for the request.

        Returns:
            Result: The result of the API request.
        """
        return await self._do("POST", endpoint=endpoint, json_data=json_data)
