from view.cli_view import CLIView

class AppController:
    def __init__(self):
        self.view = CLIView()

    def run(self):
        self.view.show_welcome()

        while True:
            choice = self.view.prompt_main_menu()

            # if choice == "1":
            #     data = self.