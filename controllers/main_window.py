from controllers.authentication_manager import AuthenticationManager
from models.my_text_edit import MyTextEdit
from utils.constants import *
from utils.supabase_client import supabase

import socket
import threading
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox, QTextEdit, QVBoxLayout
from PyQt5.uic import loadUi

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Create a stacked widget
        self.stacked_widget = QStackedWidget()

        # Load the login and signup pages from their respective UI files
        self.login_page = loadUi('ui/login.ui')
        self.signup_page = loadUi('ui/signup.ui')
        self.navbar = loadUi('ui/navbar.ui')

        # Add the pages to the stacked widget
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.signup_page)
        self.stacked_widget.addWidget(self.navbar)

        # Set the central widget as the stacked widget
        self.setCentralWidget(self.stacked_widget)

        # Create an instance of the AuthenticationManager
        self.auth_manager = AuthenticationManager()

        # Connect the signal for switching to the signup page
        self.login_page.signUpLabel.mousePressEvent = self.switch_to_signup
        self.signup_page.logInLabel.mousePressEvent = self.switch_to_login

        # Connect the signup function to the signup button
        self.signup_page.pushButtonEmail.clicked.connect(self.signup)
        self.login_page.pushButtonEmail.clicked.connect(self.login)
        self.login_page.pushButtonGoogle.clicked.connect(self.signinGoogle)
        
         # Establish a socket connection to the server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect(('127.0.0.1', 5555))
        
        # Remove the existing textEdit from the layout
        existing_text_edit = self.navbar.textEdit
        self.navbar.verticalLayout.removeWidget(existing_text_edit)
        existing_text_edit.setParent(None)

        # Create an instance of MyTextEdit with the server socket
        self.text_edit = MyTextEdit(self.server_socket)  # Create an instance of MyTextEdit
        self.navbar.verticalLayout.addWidget(self.text_edit)
        
        # self.text_edit.textChanged.connect(self.text_edit.send_data)

        # Start a thread to continuously listen for changes in the textEdit
        print("Starting thread in self to listen for changes in the textEdit.....")
        threading.Thread(target=self.listen_for_changes).start()
        
    def fetch_and_update_content(self):
        try:
            # Fetch the latest content based on the doc_id
            doc_id_query = supabase.table('docs').select('content').eq('doc_id', docId2).execute()
            if doc_id_query and doc_id_query.data:
                latest_content = doc_id_query.data[0]['content']
                
                # Update the text_edit only if the content has changed
                if latest_content != self.text_edit.toPlainText():
                    self.text_edit.setPlainText(latest_content)
                    print("Content updated.")

        except Exception as e:
            print(f"An error occurred during fetch_and_update_content: {e}")

    def start_sync_timer(self):
        # Set up a QTimer to periodically fetch and update content
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.fetch_and_update_content)
        self.sync_timer.start(1)  # Adjust the interval as needed (in milliseconds)
        print("Sync timer started.")

    def update_text_edit(self):
        try:
            # Fetch user data from Supabase 'users' table
            response = supabase.table('users').select("*").execute()
            
            self.navbar.textEdit.setPlainText(f"response: {response}")

        except Exception as e:
            print(f"An error occurred during update_text_edit: {e}")
    def switch_to_navbar(self, response):

        # Switch to the home page
        self.stacked_widget.setCurrentIndex(2)
        user_name = response.user.user_metadata.get('name').split(" ")[0]
        self.navbar.label.setText(f"Hi {user_name}!")

        # Connect the textChanged signal to the send_data method
        if not hasattr(self.text_edit, 'connected'):
            # Connect the textChanged signal to the send_data method
            self.text_edit.textChanged.connect(self.text_edit.send_data)
            # Mark the connection as established
            self.text_edit.connected = True
        
        # self.update_text_edit()
        
    def listen_for_changes(self):
        try:
            # global realtime
            # realtime = supabase.realtime()

            # Subscribe to changes in the 'docs' table for the specific 'doc_id'
            # print("\nThe realtime is: " + realtime) 
            # print("\nThe doc id is: " + docId2)
            # realtime.on('docs:doc_id=eq.' + docId2, self.handle_realtime_update)

            # while True:
            #     # Keep the event loop running
            #     QApplication.processEvents()
            #     time.sleep(0.1)
            while True:
                # Receive data from the server
                data = self.server_socket.recv(1024)
                if not data:
                    break

                # # Update the textEdit in the navbar with the received data
            received_text = data.decode('utf-8')
            self.text_edit.setPlainText(received_text)
                # # supabase.table('users').update({
                # # supabase.table('docs').insert([{'doc_id': doc_id}, {'users': [response.user.id]}]).execute()
                # supabase.table('docs').update({'content': received_text}).eq('doc_id', docId).execute()                

        except Exception as e:
            print(f"An error occurred during listen_for_changes: {e}")
    
    # def handle_realtime_update(self, payload):
    #     try:
    #         # Update the textEdit in the navbar with the received data
    #         received_text = payload['new']['content']
    #         self.text_edit.setPlainText(received_text)

    #     except Exception as e:
    #         print(f"An error occurred during handle_realtime_update: {e}")
                
    def switch_to_signup(self, event):
        if event.button() == Qt.LeftButton:
            # Switch to the signup page
            self.stacked_widget.setCurrentIndex(1)

    def switch_to_login(self, event):
        if event.button() == Qt.LeftButton:
            # Switch to the login page
            self.stacked_widget.setCurrentIndex(0)

    def signup(self):
        full_name = self.signup_page.lineEditFullName.text()
        email = self.signup_page.lineEditEmail.text()
        password = self.signup_page.lineEditPassword.text()

        response = self.auth_manager.signup(email, password, full_name, self.stacked_widget)

        if response:
            self.switch_to_navbar(response)

    def login(self):
        email = self.login_page.lineEditEmail.text()
        password = self.login_page.lineEditPassword.text()

        response = self.auth_manager.login(email, password)

        if response:
            self.switch_to_navbar(response)
            
    def signinGoogle(self):
        # email = self.login_page.lineEditEmail.text()
        # password = self.login_page.lineEditPassword.text()

        response = self.auth_manager.signinWithGoogle()

        if response:
            print(response)
            self.switch_to_navbar(response)


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    
     # Start a thread to continuously listen for changes in the textEdit
    # print("Starting thread to listen for changes in the textEdit.....")
    # threading.Thread(target=main_window.listen_for_changes).start()
    main_window.start_sync_timer()
    
    main_window.show()
    app.exec_()

# MainWindow.listen_for_changes()