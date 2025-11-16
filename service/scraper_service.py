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
        # print(f"[DEBUG] 스크래핑 URL: {url}")
        # print(f"[DEBUG] 쿠키 개수: {len(cookies)}")

        if not cookies:
            print("[ERROR] 쿠키가 없습니다! 브라우저에서 디스코드에 로그인되어 있는지 확인하세요.")
            return []

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            response = requests.get(url, cookies=cookies, headers=headers)
            # print(f"[DEBUG] HTTP 상태 코드: {response.status_code}")

            if response.status_code != 200:
                print(f"[ERROR] 로그인 안 된 세션이거나 접근 불가: {response.status_code}")
                # print(f"[DEBUG] 응답 내용 일부: {response.text[:200]}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            # print("[DEBUG] HTML 파싱 완료")

            posts = []
            # TODO: 실제 스크래핑 로직 구현 필요
            # print("[DEBUG] 스크래핑 로직 구현 필요")
            
            return posts
        except Exception as e:
            print(f"[ERROR] 스크래핑 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return []
