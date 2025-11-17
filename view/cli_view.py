
class CLIView:
    def show_welcome(self):
        print("\n<디스코드 데이터 수집>")

    def prompt_main_menu(self):
        print("\n메뉴 선택:")
        print("1. 디스코드 글/ 댓글 스크래핑 (자동 분류)")
        print("2. 디스코드 글/ 댓글 스크래핑 (배치 분류용)")
        print("3. 배치 분류 실행")
        print("4. 스크래핑된 데이터 보기")
        print("5. CSV 저장")
        print("0. 종료")
        return input("> ")

    def show_message(self, msg):
        print(f"[+] {msg}")

    def show_error(self, err):
        print(f"[ERROR] {err}")