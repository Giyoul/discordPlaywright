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
            
            if self._process_choice(choice):
                break

    def _process_choice(self, choice):
        handlers = {
            "1": self._handle_auto_classify_scrape,
            "2": self._handle_batch_scrape,
            "3": self._handle_batch_classify,
            "4": self._handle_show_data,
            "5": self._handle_save_csv,
            "0": self._handle_exit
        }
        
        handler = handlers.get(choice)
        if handler:
            return handler()
        else:
            self.view.show_error("잘못된 입력입니다!")
            return False

    def _handle_auto_classify_scrape(self):
        self.scraper.set_auto_classify(True)
        self.scraper.scrape()
        self.view.show_message("스크래핑 완료!")
        return False

    def _handle_batch_scrape(self):
        self.scraper.set_auto_classify(False)
        self.scraper.scrape()
        self.view.show_message("스크래핑 완료! (원본 데이터 저장됨)")
        return False

    def _handle_batch_classify(self):
        self.scraper.batch_classify()
        self.view.show_message("배치 분류 완료!")
        return False

    def _handle_show_data(self):
        self.scraper.show_scraped_data_summary()
        return False

    def _handle_save_csv(self):
        self.save_service.save_to_csv()
        return False

    def _handle_exit(self):
        self.view.show_message("종료합니다!")
        return True
