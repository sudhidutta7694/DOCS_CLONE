import bcrypt
import time
import socket
import threading
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox, QTextEdit, QVBoxLayout
from PyQt5.uic import loadUi
from supabase import create_client
import webbrowser
from credentials import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
docId = None
docId2 = None
userId = None
realtime = None
class AuthenticationManager:
    @staticmethod
    def signinWithGoogle():
        try:
            response = supabase.auth.sign_in_with_oauth({
                "provider": 'google',
            })
            if response and response.url:
                # AuthenticationManager.show_popup("Google Sign In", response.get("url"))
                webbrowser.open(response.url) 
            print("Signup successful!")
            return response

        except Exception as e:
            print(f"An error occurred during signup: {e}")
    @staticmethod
    def signup(email, password, full_name, stacked_widget):
        try:
            response = supabase.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': {
                        'name': full_name
                    }
                }
            })
            
            if response:
                user_data = {
                    'uid': response.user.id,
                    'full_name': full_name,
                    'email': email,
                    'password': MainWindow.hash_password(password).decode('utf-8')  # Note: Make sure to hash the password before storing it
                }
                supabase.table('users').insert([user_data]).execute()

                AuthenticationManager.show_popup("Signup Successful", "User registered successfully.")
                
                doc_id = supabase.table('users').select('docs').eq('uid', response.user.id).execute().data[0]['docs']
                
                # print("doc_id: ", doc_id.data[0]['docs'])
                
                supabase.table('docs').insert([{'doc_id': doc_id, 'users': [response.user.id]}]).execute()

                
                global docId
                docId = doc_id
                # Redirect to the login page or perform any other action as needed
                stacked_widget.setCurrentIndex(0)

            print("Signup successful!")
            # print(response.user.id)
            return response

        except Exception as e:
            print(f"An error occurred during signup: {e}")

    @staticmethod
    def show_popup(title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()

    @staticmethod
    def login(email, password):
        try:
            response = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password,
            })

            print("Login successful!")
            global userId
            userId = response.user.id
            return response

        except Exception as e:
            print(f"An error occurred during login: {e}")

class MyTextEdit(QTextEdit):
    def __init__(self, server_socket):
        super().__init__()

        self.server_socket = server_socket

        self.textChanged.connect(self.send_data)

    def send_data(self):
        text = self.toPlainText()
        if (docId == None) : 
            # Use Supabase query to get the doc_id where the users array contains the logged-in user ID
            doc_id_query = supabase.table('docs').select('doc_id').contains('users', [userId]).execute()

            # Assuming the result is a list of rows, get the doc_id from the first row (if available)
            if doc_id_query and doc_id_query.data:
                doc_id = doc_id_query.data[0]['doc_id']
                global docId2
                docId2 = doc_id
                # print(f"Doc ID for the logged-in user: {doc_id}")
                supabase.table('docs').update({'content': text}).eq('doc_id', doc_id).execute()
                self.server_socket.sendall(text.encode())
                
            else:
                print("No matching document found for the logged-in user.")
        else :
            supabase.table('docs').update({'content': text}).eq('doc_id', docId).execute()
            self.server_socket.sendall(text.encode())
        
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Create a stacked widget
        self.stacked_widget = QStackedWidget()

        # Load the login and signup pages from their respective UI files
        self.login_page = loadUi('ui/login.ui')
        self.signup_page = loadUi('ui/signup.ui')
        self.navbar = loadUi('ui/nav_new.ui')

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
    @staticmethod
    def hash_password(password):
    # Generate a random salt using the secrets module
        salt = bcrypt.gensalt()

    # Hash the password using bcrypt and the generated salt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

        return hashed_password
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