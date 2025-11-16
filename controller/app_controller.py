from view.cli_view import CLIView

class AppController:
    def __init__(self):
        self.view = CLIView()

    def run(self):
        self.view.show_welcome()
