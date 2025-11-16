import browser_cookie3

class AuthService:
    def __init__(self):
        self.cookie_dict = None

    def load_browser_cookies(self):
        try:
            print("브라우저 쿠키 불러오는 중...")
            cookies = browser_cookie3.chrome(domain_name="discord.com")
            self.cookie_dict = {}
            for cookie in cookies:
                self.cookie_dict[cookie.name] = cookie.value
            print("쿠키 불러오기 성공!")
        except Exception as e:
            print("쿠키 로드 실패:", e)
            self.cookie_dict = None

    def get_cookies(self):
        if self.cookie_dict is None:
            self.load_browser_cookies()
        
        if self.cookie_dict is None:
            self.cookie_dict = {}

        return self.cookie_dict