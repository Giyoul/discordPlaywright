from view.cli_view import CLIView
from service.scraper_service import ScraperService
from service.save_service import SaveService

class AppController:
    def __init__(self):
        self.view = CLIView()
        self.scraper = ScraperService()
        self.save_service = SaveService(self.scraper, self.view)



    def run(self):
        self.view.show_welcome()

        while True:
            choice = self.view.prompt_main_menu()

            if choice == "1":
                # 자동 분류 모드
                self.scraper.set_auto_classify(True)
                data = self.scraper.scrape()
                self.view.show_message("스크래핑 완료!")

            elif choice == "2":
                # 배치 분류 모드 (분류하지 않고 원본만 저장)
                self.scraper.set_auto_classify(False)
                data = self.scraper.scrape()
                self.view.show_message("스크래핑 완료! (원본 데이터 저장됨)")

            elif choice == "3":
                # 배치 분류 실행
                self.scraper.batch_classify()
                self.view.show_message("배치 분류 완료!")

            elif choice == "4":
                self.save_service.save_to_csv()

            elif choice == "0":
                self.view.show_message("종료합니다!")
                break

            else:
                self.view.show_error("잘못된 입력입니다!")
    
