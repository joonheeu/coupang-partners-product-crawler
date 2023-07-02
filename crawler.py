import json
import os
import requests
import urllib.parse
import logging
from pprint import pprint
from dotenv import load_dotenv


LOGIN_URL         = "https://login.coupang.com/login/login.pang"
LOGIN_PROCESS_URL = "https://login.coupang.com/login/loginProcess.pang"
POSTLOGIN_URL     = "https://partners.coupang.com/api/v1/postlogin"
SEARCH_URL        = "https://partners.coupang.com/api/v1/search"
BANNER_URL        = "https://partners.coupang.com/api/v1/banner/iframe/url"

class CoupangPartnersCrawler(requests.Session):
    """
    쿠팡 파트너스 웹사이트의 크롤러입니다.
    A crawler for the Coupang Partners website.

    Args:
        username (str): The username for logging into Coupang Partners.
        password (str): The password for logging into Coupang Partners.
        user_agent (str, optional): The user agent string for the crawler. Defaults to None.
    """

    def __init__(self, username: str, password: str, user_agent: str = None) -> None:
        """
        CoupangPartnersCrawler 인스턴스를 초기화합니다.
        Initialize the CoupangPartnersCrawler instance.

        Args:
            username (str): The username for logging into Coupang Partners.
            password (str): The password for logging into Coupang Partners.
            user_agent (str, optional): The user agent string for the crawler. Defaults to None.
        """
        super().__init__()
        self.username: str = username
        self.password: str = password
        self.token: str = None
        self.user_agent: str = user_agent or "Mozilla/5.0 (Linux; Android 13; Redmi Note 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Mobile Safari/537.36"
        self.logger: logging.Logger = logging.getLogger("CoupangPartnersCrawler")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler())

    def __get_headers(self, headers: dict = None) -> dict:
        """
        HTTP 요청에 대한 헤더를 가져옵니다.
        Get the headers for HTTP requests.

        Args:
            headers (dict, optional): Additional headers to include. Defaults to None.

        Returns:
            dict: The headers for the request.
        """
        default_headers: dict = {
            "User-Agent": self.user_agent,
            "accept-language": "ko,ko-KR;q=0.9,en;q=0.8,en-US;q=0.7"
        }
        return {**default_headers, **(headers or {})}

    def __get_token(self) -> str:
        """
        Cookies에서 인증 토큰을 가져옵니다.
        Get the authentication token from cookies.

        Returns:
            str: The authentication token.
        """
        return self.cookies.get('AFATK')

    def __get(self, url: str, headers: dict = None) -> requests.Response:
        """
        GET 요청을 보냅니다.
        Send a GET request.

        Args:
            url (str): The URL to send the request to.
            headers (dict, optional): Additional headers to include. Defaults to None.

        Returns:
            requests.Response: The response object.
        """
        try:
            response: requests.Response = self.get(url, headers=headers or self.__get_headers())
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"GET request failed: {e}")
            raise

    def __post(self, url: str, headers: dict = None, data: str = None, json_data: dict = None, allow_redirects: bool = None) -> requests.Response:
        """
        POST 요청을 보냅니다.
        Send a POST request.

        Args:
            url (str): The URL to send the request to.
            headers (dict, optional): Additional headers to include. Defaults to None.
            data (str, optional): The request body as a string. Defaults to None.
            json_data (dict, optional): The request body as a JSON object. Defaults to None.
            allow_redirects (bool, optional): Whether to allow redirects. Defaults to None.

        Returns:
            requests.Response: The response object.
        """
        try:
            response: requests.Response = self.post(url, headers=headers or self.__get_headers(), data=data, json=json_data, allow_redirects=allow_redirects)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"POST request failed: {e}")
            raise

    def login(self) -> None:
        """
        Login to Coupang Partners.
        """
        self.__get(LOGIN_URL)
        headers: dict = self.__get_headers({"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        data: str = urllib.parse.urlencode({"email": self.username, "password": self.password})
        self.__post(LOGIN_PROCESS_URL, headers=headers, data=data, allow_redirects=True)
        self.__get(POSTLOGIN_URL)
        self.token = self.__get_token()
        self.logger.debug(f"Token: {self.token}")
        
        return self.token is not None
        
    def search_keyword(self, keyword: str) -> list:
        """
        Search for products by keyword.

        Args:
            keyword (str): The keyword to search for.

        Returns:
            list: The list of products matching the keyword.
        """
        headers: dict = self.__get_headers({"Content-Type": "application/json;charset=UTF-8", "X-Token": self.token})
        data: str = json.dumps({"filter": keyword, "page": {"pageNumber": 0, "size": 36}})
        response: requests.Response = self.__post(SEARCH_URL, headers=headers, data=data)
        products: list = response.json()['data']['products']
        return products

    def get_link(self, product: dict) -> str:
        """
        Get the short URL for a product.

        Args:
            product (dict): The product information.

        Returns:
            str: The short URL of the product.
        """
        headers: dict = self.__get_headers({'content-type': 'application/json;charset=UTF-8', "X-Token": self.token})
        json_data: dict = {'product': product}
        response: requests.Response = self.__post(BANNER_URL, headers=headers, json_data=json_data)
        return response.json()['data']['shortUrl']
    

if __name__ == "__main__":
    # Get account from CoupangPartners from the .env file
    load_dotenv()
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    print(f'username: {username}')

    # Create an instance of CoupangPartnersCrawler
    crawler = CoupangPartnersCrawler(username, password)

    # Login to Coupang Partners
    if not crawler.login():
        raise Exception("Login failed. Please check your username and password.")

    # Search for products by keyword
    keyword = "신발"
    products = crawler.search_keyword(keyword)
    print(f"Products matching the keyword '{keyword}':")
    for product in products:
        pprint(product)

    # Get the short URL for a product
    product = products[0]
    short_url = crawler.get_link(product)
    print(f"Short URL for the product: {short_url}")
