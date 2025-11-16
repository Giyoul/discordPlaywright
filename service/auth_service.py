import browser_cookie3

class AuthService:
    def __init__(self):
        self.cookies = None

    def load_browser_cookies(self):
        try:
            print("브라우저 쿠키 불러오는 중...")
            self.cookies = browser_cookie3.Chrome()
            print("쿠키 불러오기 성공!")
        except Exception as e:
            print("쿠키 로드 실패:", e)

    def get_cookies(self):
        if self.cookies is None:
            self.load_browser_cookies()
        # browser_cookie3 객체를 딕셔너리로 변환
        cookie_dict = {}
        if self.cookies:
            for cookie in self.cookies:
                cookie_dict[cookie.name] = cookie.value
        return cookie_dict