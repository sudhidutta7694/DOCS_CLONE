import bcrypt
import uuid
import socket
import threading
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
import webbrowser
from utils.supabase_client import supabase

docId = None
userId = None
username = None

class AuthenticationManager:
    @staticmethod
    def signinWithGoogle():
        try:
            response = supabase.auth.sign_in_with_oauth({
                "provider": 'google',
            })
            if response and response.url:
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
                
                # print("doc_id: ", doc_id.data[0]['docs'])
                global userId
                userId = response.user.id
                global username
                username = response.user.user_metadata.get('name').split(" ")[0]
                # Redirect to the login page or perform any other action as needed
                # stacked_widget.setCurrentIndex(0)

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
            AuthenticationManager.show_popup("Login Successful", "User logged in.")
            global userId
            userId = response.user.id
            # global docId
            # docId = supabase.table('users').select('docs').eq('uid', response.user.id).execute().data[0]['docs']
            global username
            username = response.user.user_metadata.get('name').split(" ")[0]
                
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
        self.home_page = loadUi('ui/home.ui')
        self.navbar = loadUi('ui/navbar.ui')

        # Add the pages to the stacked widget
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.signup_page)
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.navbar)

        # Set the central widget as the stacked widget
        self.setCentralWidget(self.stacked_widget)

        # Create an instance of the AuthenticationManager
        self.auth_manager = AuthenticationManager()

        # Connect the signal for switching to the signup page
        self.login_page.signUpLabel.mousePressEvent = self.switch_to_signup
        self.signup_page.logInLabel.mousePressEvent = self.switch_to_login
        # self.home_page.pushButton.mousePressEvent = self.switch_to_navbar
        # self.home_page.pushButton.clicked.connect(lambda: self.switch_to_navbar(response))


        # Connect the signup function to the signup button
        self.signup_page.pushButtonEmail.clicked.connect(self.signup)
        self.login_page.pushButtonEmail.clicked.connect(self.login)
        self.login_page.pushButtonGoogle.clicked.connect(self.signinGoogle)
        self.home_page.pushButton.clicked.connect(self.create_doc)
        
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
            doc_id_query = supabase.table('docs').select('content').eq('doc_id', docId).execute()
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
            # Fetch initial content from Supabase 'docs' table
            initial_data = supabase.table('docs').select('content').eq('doc_id', docId).execute().data[0]['content']
            print("\nInitial data: \n", initial_data)
            self.text_edit.setPlainText(initial_data)
            self.start_sync_timer()

        except Exception as e:
            print(f"An error occurred during initial_update_text_edit: {e}")
    @staticmethod
    def hash_password(password):
    # Generate a random salt using the secrets module
        salt = bcrypt.gensalt()

    # Hash the password using bcrypt and the generated salt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

        return hashed_password
    def switch_to_home(self):
        # Switch to the navbar page when the button on the home page is clicked
        
        self.stacked_widget.setCurrentIndex(2)
        self.home_page.label_4.setText(f"Hi {username}!")
        self.update_ui()
    def generate_doc_id():
        doc_id = str(uuid.uuid4())
        return doc_id
    def create_doc(self):
        new_doc_id = MainWindow.generate_doc_id()
        doc_name, ok = QInputDialog.getText(self, 'New Document', 'Enter document name:')
        if ok and doc_name:
            uuids = supabase.table('users').select('docs').eq('uid', userId).execute().data[0]['docs']
            print(f'existing_uuids: {uuids}')
            if uuids is not None:
                uuids.append(new_doc_id)
            else :
                uuids = [new_doc_id]
            print(f'uuids: {uuids}')
            supabase.table('users').update({'docs': uuids}).eq('uid', userId).execute().data[0]['docs']
            global docId
            docId = new_doc_id
            supabase.table('docs').insert([{'doc_id': new_doc_id, 'name': doc_name, 'users': [userId]}]).execute()
            self.switch_to_navbar(doc_name)
    def fetch_docs(self):
        try:
            # Fetch document names from the Supabase 'docs' table
            docs_data = supabase.table('docs').select('name').contains('users', [userId]).execute().data

            return [doc['name'] for doc in docs_data] if docs_data else []

        except Exception as e:
            print(f"An error occurred during fetch_docs: {e}")
            return []

    def update_ui(self):
        # Clear existing widgets from the layout
        for i in reversed(range(self.home_page.horizontalLayoutDocs.count())):
            self.home_page.horizontalLayoutDocs.itemAt(i).widget().setParent(None)

        # Fetch document names
        doc_names = self.fetch_docs()
        print("Fetching document names: ", doc_names)

        # Create and add widgets to the layout
        for doc_name in doc_names:
            doc_widget = self.create_doc_widget(doc_name)
            self.home_page.horizontalLayoutDocs.addWidget(doc_widget)

    # def create_doc_widget(self, doc_name):
    #     # Create a widget for each document
    #     doc_widget = QWidget()
    #     doc_layout = QVBoxLayout()

    #     # Create a label for the document name
    #     doc_label = QLabel(doc_name)
    #     doc_label.setStyleSheet("font-size: 14px; font-weight: bold;")

    #     # Add the label to the layout
    #     doc_layout.addWidget(doc_label)

    #     # Set the layout for the widget
    #     doc_widget.setLayout(doc_layout)

    #     return doc_widget        
    def create_doc_widget(self, doc_name):
    # Create a frame to encapsulate each document's information
        doc_frame = QFrame()
        doc_frame.setFrameShape(QFrame.Box)  # Set the frame shape
        doc_frame.setLineWidth(1)  # Set the frame line width

        # Create a button for the document
        doc_button = QPushButton(doc_name)
        doc_button.clicked.connect(lambda _, name=doc_name: self.open_doc(name))

        # Set up a vertical layout for the frame and add the button
        frame_layout = QVBoxLayout()
        frame_layout.addWidget(doc_button)
        doc_frame.setLayout(frame_layout)

        return doc_frame
    def open_doc(self, doc_name) :
        global docId
        docId = supabase.table('docs').select('doc_id').eq('name', doc_name).execute().data[0]['doc_id']
        self.switch_to_navbar(doc_name)
        
    def switch_to_navbar(self, doc_name):

        # Switch to the home page
        self.stacked_widget.setCurrentIndex(3)
        self.navbar.pushButton_6.setText(f"{doc_name}")
        self.navbar.label.setText(f"Hi {username}!")
        
        self.update_text_edit()

        # Connect the textChanged signal to the send_data method
        if not hasattr(self.text_edit, 'connected'):
            # Connect the textChanged signal to the send_data method
            self.text_edit.textChanged.connect(self.text_edit.send_data)
            # Mark the connection as established
            self.text_edit.connected = True
        
        
    def listen_for_changes(self):
        try:
            while True:
                # Receive data from the server
                data = self.server_socket.recv(1024)
                if not data:
                    break

            # Update the textEdit in the navbar with the received data
            received_text = data.decode('utf-8')
            self.text_edit.setPlainText(received_text)               

        except Exception as e:
            print(f"An error occurred during listen_for_changes: {e}")
            
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
            self.switch_to_home()

    def login(self):
        email = self.login_page.lineEditEmail.text()
        password = self.login_page.lineEditPassword.text()

        response = self.auth_manager.login(email, password)

        if response:
            self.switch_to_home()
            
    def signinGoogle(self):
        # email = self.login_page.lineEditEmail.text()
        # password = self.login_page.lineEditPassword.text()

        response = self.auth_manager.signinWithGoogle()

        if response:
            print(response)
            self.switch_to_home()


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
    
# main_window.update_ui()