import requests
import config
from bs4 import BeautifulSoup
from service.auth_service import AuthService

class ScraperService:
    def __init__(self):
        self.auth = AuthService()
        self.cached_posts = []

    def scrape(self):
        url = config.CHANNEL_URL
        cookies = self.auth.get_cookies()

        print("스크래핑 시작...")

        response = requests.get(url, cookies=cookies)

        if response.status_code != 200:
            print("로그인 안 된 세션이거나 접근 불가:", response.status_code)
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        posts = []
