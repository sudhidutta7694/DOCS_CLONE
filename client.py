import socket
from PyQt5.QtWidgets import QApplication, QTextEdit

HOST = '127.0.1.1'  # Use your server IP or 'localhost'
PORT = 5555

class MyTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))

        self.textChanged.connect(self.send_data)

    def send_data(self):
        text = self.toPlainText()
        self.socket.sendall(text.encode())

if __name__ == "__main__":
    app = QApplication([])

    text_edit = MyTextEdit()
    text_edit.show()

    app.exec_()
