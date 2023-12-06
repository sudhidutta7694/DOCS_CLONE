from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

class HomeScreen(QWidget):
    def __init__(self):
        super(HomeScreen, self).__init__()

        # Set up the layout for the home screen
        self.layout = QVBoxLayout(self)

        # Create a welcome label
        self.welcome_label = QLabel()
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.welcome_label)

        # Set the home screen background color
        self.setStyleSheet("background-color: #F9E6E6;")

    def set_welcome_message(self, username):
        # Set the welcome label text
        self.welcome_label.setText(f"Hi {username}!")

if __name__ == "__main__":
    app = QApplication([])

    # Example usage of the HomeScreen class
    home_screen = HomeScreen()
    home_screen.set_welcome_message("John Doe")
    home_screen.show()

    app.exec_()
