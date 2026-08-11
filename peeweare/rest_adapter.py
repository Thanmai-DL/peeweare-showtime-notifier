import logging
from json import JSONDecodeError

import httpx

from peeweare.exception import PeeweareException
from peeweare.models import Result


class RestAdapter:
    def __init__(
        self,
        hostname: str = "api3.pvrcinemas.com",
        ver: str = "v1",
        ssl_verify: bool = True,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the API client.

        Args:
            hostname (str): The API hostname.
            ver (str): The API version.
            ssl_verify (bool): Whether to verify SSL certificates.
            logger (logging.Logger): The logger to use.
        """
        self.base_url = f"https://{hostname}/api/{ver}/booking/content/"

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
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            #        "Content-Type": "application/json",
            "Authorization": "Bearer",
            "chain": "PVR",
            "city": "Bengaluru",
            "appVersion": "1.0",
            "platform": "WEBSITE",
            "country": "INDIA",
            "flow": "PVRINOX",
            "Origin": "https://www.pvrcinemas.com",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "TE": "trailers",
        }

        log_line_pre = f"method={http_method}, url={url}"
        log_line_post = f"{log_line_pre}, success={{}}, status_code={{}}, message={{}}"

        try:
            self._logger.debug(msg=log_line_pre)
            async with httpx.AsyncClient(verify=self._ssl_verify) as client:
                response = await client.request(
                    method=http_method, url=url, headers=headers, json=json_data, timeout=None
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

    async def get(self, endpoint: str, json_data: dict[str, str] | None = None) -> Result:
        """
        Perform a GET request to the API.

        Args:
            endpoint (str): The API endpoint.
            json_data (Dict[str, str], optional): The JSON data for the request.

        Returns:
            Result: The result of the API request.
        """
        return await self._do("GET", endpoint=endpoint, json_data=json_data)

    async def post(self, endpoint: str, json_data: dict[str, str] | None = None) -> Result:
        """
        Perform a POST request to the API.

        Args:
            endpoint (str): The API endpoint.
            json_data (Dict[str, str], optional): The JSON data for the request.

        Returns:
            Result: The result of the API request.
        """
        return await self._do("POST", endpoint=endpoint, json_data=json_data)
