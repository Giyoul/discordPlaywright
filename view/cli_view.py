
class CLIView:
    def show_welcome(self):
        print("\n<디스코드 데이터 수집>")

    def prompt_main_menu(self):
        print("\n메뉴 선택:")
        print("1. 디스코드 글/ 댓글 스크래핑")
        print("2. 카테고리 분류")
        print("3. CSV 저장")
        print("0. 종료")
        return input("> ")

    def show_message(self, msg):
        print(f"[+] {msg}")

    def show_error(self, err):
        print(f"[ERROR] {err}")

    def show_login_session_certificate(self):
        print("로그인 세션을 확인하는 중... (브라우저 쿠키 사용)")