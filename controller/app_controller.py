from view.cli_view import CLIView
from service.scraper_service import ScraperService

class AppController:
    def __init__(self):
        self.view = CLIView()
        self.scraper = ScraperService()



    def run(self):
        self.view.show_welcome()
        self.certificate()

        while True:
            choice = self.view.prompt_main_menu()

            if choice == "1":
                data = self.scraper.scrape()
                self.view.show_message("스크래핑 완료!")

            elif choice == "2":
                # 카테고리 분류 기능 구현

                self.view.show_message("카테고리 분류 완료!")

            elif choice == "3":
                # CSV 파일로 저장 기능 구현

                self.view.show_message("CSV 파일 저장 완료!")

            elif choice == "0":
                self.view.show_message("종료합니다!")
                break

            else:
                self.view.show_error("잘못된 입력입니다!")

    def certificate(self):
        self.view.show_login_session_certificate()
        self.scraper.auth.load_browser_cookies()

    # def
    # 여기 반복문 객체화