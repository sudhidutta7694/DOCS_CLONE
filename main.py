import bcrypt
import sys
import os
import smtplib
from email.mime.text import MIMEText
import uuid
import socket
import threading
import cloudinary.uploader, requests
from cloudinary_credentials import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
import webbrowser
from utils.supabase_client import supabase
from credentials import *
from PyQt5.QtPrintSupport import QPrinter
import html_previewer_copy as html_previewer

docId = None
userId = None
username = None
docName = None

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
    def logout(self):
        try:
            response = supabase.auth.sign_out()
            print("Logout successful!")
            AuthenticationManager.show_popup("Logout Successful", "User logged out.")
            return response
        except Exception as e:
            print(f"An error occurred during logout: {e}")

class MyTextEdit(QTextEdit):
    def __init__(self, server_socket):
        super().__init__()

        self.server_socket = server_socket
        self.cursorPositionChanged.connect(self.send_data)
       
    def send_data(self):
        try:
            html = self.toHtml()

            # Update Supabase table
            supabase.table('docs').update({'content': html}).eq('doc_id', docId).execute()

            # Check if the socket is not initialized or closed
            if not self.server_socket or self.server_socket.fileno() == -1:
                # Re-establish the socket connection
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect(('127.0.0.1', 5555))

            # Use invokeMethod to ensure the slot is executed in the main thread
            QMetaObject.invokeMethod(self, "send_to_server", Qt.QueuedConnection, Q_ARG(str, html))
        except Exception as e:
            print(f"An error occurred during send_data: {e}")
    @pyqtSlot(str)
    def send_to_server(self, html):
        # Send HTML data to the server socket
        self.server_socket.sendall(html.encode())
            
class ShareDialog(QDialog):
    def __init__(self, doc_name):
        super(ShareDialog, self, ).__init__()
        loadUi('ui/share.ui', self)
        self.doc_name = doc_name
        doc_id = supabase.table('docs').select('doc_id').eq('name', doc_name).execute().data[0]['doc_id']
        self.doc_id = doc_id
        self.setWindowTitle(doc_name)
        self.labelShare.setText(f"Share '{doc_name}'")

        # Fetch users from the docs_table and update the UI
        self.update_user_list()
        self.pushButtonCopy.clicked.connect(MainWindow.copy_access_link)
        self.pushButtonDone.clicked.connect(self.get_share_info)
        
    def update_user_list(self):
        # Replace with your actual logic to fetch users from the docs_table
        # For demonstration, I'm assuming a list of user UUIDs
        user_uuids = supabase.table('docs').select('users').eq('doc_id', docId).execute().data[0]['users']
        

        # Clear existing widgets from the layout
        for i in reversed(range(self.verticalLayout.count())):
            self.verticalLayout.itemAt(i).widget().setParent(None)

        # Create and add widgets for each user
        for idx, user_uuid in enumerate(user_uuids):
            user_widget = self.create_user_widget(user_uuid, idx == 0)
            self.verticalLayout.addWidget(user_widget)

    def create_user_widget(self, user_uuid, is_owner):
        # Fetch user data (replace with your actual logic)
        user_name = self.get_user_name(user_uuid)
        # Load user profile picture (replace with your actual logic)
        profile_picture_path = "resources/images/user.png"

        # Create a widget for each user
        user_widget = QWidget()
        user_layout = QHBoxLayout()  # Use QHBoxLayout to place items horizontally

        # Create a label for the user profile picture
        profile_picture_label = QLabel()
        pixmap = QPixmap(profile_picture_path)
        profile_picture_label.setPixmap(pixmap)
        profile_picture_label.setFixedWidth(20)
        profile_picture_label.setFixedHeight(20)
        profile_picture_label.setScaledContents(True)

        # Create a label for the user name
        user_name_label = QLabel(f"{user_name} (Owner)" if is_owner else user_name)

        # Create a combo box for choosing access (if not the owner)
        # access_combo_box = QComboBox()
        # access_options = ["Restricted", "Reader", "Writer"]
        # access_combo_box.addItems(access_options)
        # access_combo_box.setEnabled(not is_owner)  # Disable for the owner
        # email = supabase.table('users').select('email').eq('uid', user_uuid).execute().data[0]['email']
        # access_combo_box.currentIndexChanged.connect(lambda mailId=email, access_type=access_combo_box.currentText(), uuid=self.doc_id: self.grant_access(mailId, access_type, uuid))
        # AuthenticationManager.show_popup("Access", f"Access {access_combo_box.currentText()} granted to {email}")

        # Add the labels and combo box to the layout
        user_layout.addWidget(profile_picture_label)
        user_layout.addWidget(user_name_label)
        # user_layout.addWidget(access_combo_box)

        # Set the layout for the widget
        user_widget.setLayout(user_layout)

        return user_widget

    def get_user_name(self, user_uuid):
        user_name = supabase.table('users').select('full_name').eq('uid', user_uuid).execute().data[0]['full_name']
        return user_name
    
    def get_share_info(self):
        email = self.lineEdit.text()
        access_type = self.comboBox.currentText()
        if email and access_type:
            self.grant_access(email, access_type, self.doc_id)
            if access_type=="Readable":
                access_type = "read"
            elif access_type=="Writable":
                access_type = "write"
            access_link = MainWindow.generate_general_access_link(self,self.doc_id, access_type)
            self.send_email(email, self.doc_name, access_link)
    
    def grant_access(self, email, access_type, doc_id):
        try:
            # Fetch user ID from the users table based on the provided email
            user_id_query = supabase.table('users').select('uid').eq('email', email).execute()
            user_id = user_id_query.data[0]['uid'] if user_id_query and user_id_query.data else None
                
            if user_id:
                # Update the docs table with the new user and access information
                current_users_query = supabase.table('docs').select('users').eq('doc_id', doc_id).execute()
                current_users = current_users_query.data[0]['users'] if current_users_query and current_users_query.data else []
                    
                # Add the new user and access information
                if user_id not in current_users: current_users.append(user_id)
                user_access_query = supabase.table('docs').select('user_access').eq('doc_id', doc_id).execute()
                current_user_access = user_access_query.data[0]['user_access'] if user_access_query and user_access_query.data else {}
                current_user_access[user_id] = access_type
                # user_access = {user_id: access_type}

                if access_type == "Restricted":
                    current_users.remove(user_id)
                    
                # Update the docs table
                supabase.table('docs').update({'users': current_users}).eq('doc_id', doc_id).execute()
                supabase.table('docs').update({'user_access': current_user_access}).eq('doc_id', doc_id).execute()
                self.update_user_list()
                # MainWindow.update_text_edit(self=MainWindow)

                if (access_type == "Restricted"):
                    print(f"Access revoked for {email}")
                    AuthenticationManager.show_popup("Access Revoked", f"Access revoked for {email}")
                    
                else:
                    print(f"Access granted to {email}")

            else:
                print("User not found.")
            

        except Exception as e:
            print(f"An error occurred: {e}")
     
    def send_email(self, to_email, doc_name, access_link):
        try:
            if str(access_link).endswith("Restricted"): 
                return
            # Set up your email server and credentials
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587  # Update with the appropriate port
            smtp_username = google_username
            smtp_password = google_password
            
            # Set up the message
            subject = f"Access to Document: {doc_name}"
            content = f"You have been granted access. Copy the link below to access the document:\n\n{access_link}"
            sender_email = supabase.table('users').select('email').eq('uid', userId).execute().data[0]['email']
            print(f"\nSender Email: {sender_email}")
            
            message = MIMEText(content)
            message['Subject'] = subject
            message['From'] = sender_email
            message['To'] = to_email

            # Connect to the SMTP server and send the email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Use this line if your server requires TLS
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, to_email, message.as_string())
                
            print(f"Email sent to {to_email}")

            AuthenticationManager.show_popup("Email Sent",f"Email sent to {to_email}")
        except Exception as e:
            print(f"An error occurred: {e}")
            AuthenticationManager.show_popup("Error", f"An error occurred: {e}")

# from PyQt5.QtWidgets import QFontDialog, QColorDialog
# from PyQt5.QtGui import QFont, QColor, QTextCharFormat

class TextEditorFunctions:
    def __init__(self, text_edit):
        self.text_edit = text_edit
        self.is_bold = False
        self.is_italic = False
        self.is_underline = False
        self.font_name = "DefaultFont"  # Set your default font name
        self.font_size = 12  # Set your default font size
        self.font_color = QColor("black")  # Set your default font color

    def make_text_bold(self):
        self.is_bold = not self.is_bold
        current_format = self.text_edit.currentCharFormat()
        font = QFont()
        font.setBold(self.is_bold)
        current_format.setFont(font)
        self.text_edit.mergeCurrentCharFormat(current_format)
        
    def make_text_italic(self):
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        char_format.setFontItalic(not char_format.fontItalic())
        cursor.mergeCharFormat(char_format)
        self.text_edit.setCurrentCharFormat(char_format)


    def make_text_underline(self):
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        char_format.setFontUnderline(not char_format.fontUnderline())
        cursor.mergeCharFormat(char_format)
        self.text_edit.setCurrentCharFormat(char_format)


    from PyQt5.QtWidgets import QFontDialog

    def show_font_dialog(self):
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        
        options = QFontDialog.DontUseNativeDialog
        font, ok = QFontDialog.getFont(char_format.font(), options=options)
        if ok:
            char_format.setFont(font)
            cursor.mergeCharFormat(char_format)
            self.text_edit.setCurrentCharFormat(char_format)


    def set_font_and_size(self, font, size):
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        char_format.setFont(font)
        char_format.setFontPointSize(size)
        cursor.mergeCharFormat(char_format)
        self.text_edit.setCurrentCharFormat(char_format)
        
    def show_color_dialog(self):
        color_dialog = QColorDialog(self.text_edit)
        color_dialog.setOption(QColorDialog.DontUseNativeDialog)  # Use this line to avoid native dialog issues
        color_dialog.currentColorChanged.connect(self.set_text_color)
        color_dialog.exec_()

    def set_text_color(self, color):
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        char_format.setForeground(color)
        cursor.mergeCharFormat(char_format)
        self.text_edit.setCurrentCharFormat(char_format)
    
class ImageHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def add_image(self):
        try:
            self.main_window.sync_timer.stop()
            file_dialog = QFileDialog()
            image_path, _ = file_dialog.getOpenFileName(self.main_window, 'Select Image', '', 'Images (*.png *.xpm *.jpg *.bmp)')

            if image_path:
                size_dialog = html_previewer.ImageSizeDialog(self.main_window)
                width, height = size_dialog.get_image_size()

                if width is not None and height is not None:
                    image_name = image_path.split('/')[-1][:-4]
                    upload_result = cloudinary.uploader.upload(image_path, public_id=image_name)

                    if 'secure_url' in upload_result:
                        hosted_url = upload_result['secure_url']
                        print("Hosted image URL:", hosted_url)

                        # Download the image to a local directory
                        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

                        # Create 'Docify/images' folder on the desktop
                        images_folder = os.path.join(desktop_path, "Docify", "images")
                        os.makedirs(images_folder, exist_ok=True)

                        # Save the image to the 'Docify/images' folder
                        local_path = os.path.join(images_folder, f"{image_name}.png")

                        response = requests.get(hosted_url, stream=True)
                        with open(local_path, 'wb') as file:
                            for chunk in response.iter_content(chunk_size=128):
                                file.write(chunk)

                        # Insert the hosted image URL into the QTextEdit
                        image_format = QTextImageFormat()
                        image_format.setWidth(width)
                        image_format.setHeight(height)
                        image_format.setName(local_path)

                        cursor = self.main_window.text_edit.textCursor()
                        cursor.insertImage(image_format)
                        # self.update_html()
        except Exception as e:
            AuthenticationManager.show_popup("Failed",f"Insertion of image failed due to {e}")    
        finally:
            self.main_window.sync_timer.start()   
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
        
        # self.html_generator = html_previewer.HtmlGenerator()
        # self.setCentralWidget(self.html_generator)
        # self.html_generator.update_html_signal.connect(self.update_database_html)

        # # Call a function to initialize the text_edit with HTML from the database
        # self.initialize_text_edit()

        # Set the central widget as the stacked widget
        self.setCentralWidget(self.stacked_widget)

        # Create an instance of the AuthenticationManager
        self.auth_manager = AuthenticationManager()
        # self.file_dialog = QFileDialog()
        self.image_handler = ImageHandler(self)

        # Connect the signal for switching to the signup page
        self.login_page.signUpLabel.mousePressEvent = self.switch_to_signup
        self.signup_page.logInLabel.mousePressEvent = self.switch_to_login
        # self.home_page.pushButton.mousePressEvent = self.switch_to_navbar
        # self.home_page.pushButton.clicked.connect(lambda: self.switch_to_navbar(response))

        # Connect the signup function to the signup button
        self.signup_page.pushButtonEmail.clicked.connect(self.signup)
        self.login_page.pushButtonEmail.clicked.connect(self.login)
        # self.login_page.pushButtonGoogle.clicked.connect(self.signinGoogle)
        self.home_page.pushButton.clicked.connect(self.create_doc)
        self.home_page.pushButtonAccess.clicked.connect(self.handle_access_link)
        self.home_page.pushButtonLogout.clicked.connect(self.logout)
        self.home_page.pushButtonRefresh.clicked.connect(self.update_ui)
        self.navbar.pushButtonBack.clicked.connect(self.switch_to_home)
        self.navbar.actionRestricted.triggered.connect(lambda: self.update_access('Restricted'))
        self.navbar.actionReadable.triggered.connect(lambda: self.update_access('Readable'))
        self.navbar.actionWritable_3.triggered.connect(lambda: self.update_access('Writable'))
        self.navbar.actionConvert_to_PDF.triggered.connect(self.convert_to_pdf)
        self.navbar.pushButtonShare.clicked.connect(lambda:self.open_share_dialog(docName))
        self.navbar.actionImage.triggered.connect(self.add_image)
        self.navbar.actionLink.triggered.connect(self.insert_link)
        self.navbar.pushButtonLink.clicked.connect(self.fetch_clickable_links)
        
         # Establish a socket connection to the server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect(('127.0.0.1', 5555))
        
        # Remove the existing textEdit from the layout
        existing_text_edit = self.navbar.textEdit
        self.navbar.verticalLayout.removeWidget(existing_text_edit)
        existing_text_edit.setParent(None)

        # Create an instance of MyTextEdit with the server socket
        self.text_edit = MyTextEdit(self.server_socket)  # Create an instance of MyTextEdit
        self.text_editor_functions = TextEditorFunctions(self.text_edit)
        self.navbar.verticalLayout.addWidget(self.text_edit)
        
        # self.text_edit.textChanged.connect(self.text_edit.send_data)
        self.navbar.pushButton.clicked.connect(self.text_editor_functions.make_text_bold)
        self.navbar.pushButton_2.clicked.connect(self.text_editor_functions.make_text_italic)
        self.navbar.pushButton_3.clicked.connect(self.text_editor_functions.make_text_underline)
        self.navbar.pushButtonColour.clicked.connect(self.text_editor_functions.show_color_dialog)
        self.navbar.pushButtonFont.clicked.connect(self.text_editor_functions.show_font_dialog)
        self.text_edit.textChanged.connect(self.text_edit_changed)

        # Start a thread to continuously listen for changes in the textEdit
        print("Starting thread in self to listen for changes in the textEdit.....")
        threading.Thread(target=self.listen_for_changes).start()
    
    def add_image(self):
        # Pause the sync timer
        self.sync_timer.stop()

        # Call the add_image method from the ImageHandler instance
        self.image_handler.add_image()

        # Resume the sync timer
        self.sync_timer.start()  
        
    def insert_link(self):
        # Create a pop-up dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Insert Link")

        # Create QLabel and QLineEdit for original text and link
        label_original = QLabel("Original Text:")
        original_text_input = QLineEdit()

        label_link = QLabel("Link:")
        link_input = QLineEdit()

        # Create OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(lambda: self.update_link(original_text_input.text(), link_input.text(), dialog))

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(label_original)
        layout.addWidget(original_text_input)
        layout.addWidget(label_link)
        layout.addWidget(link_input)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)

        # Show the dialog
        dialog.exec_()
    def update_link(self, original_text, link, dialog):
        try:
            cursor = self.text_edit.textCursor()
            cursor_position = cursor.position()

            # Insert the link in the QTextEdit at the cursor position
            cursor.insertHtml(f'<a href="{link}">{original_text}</a>')

            # Move the cursor to the end of the inserted link
            new_cursor_position = cursor_position + len(f'<a href="{link}">{original_text}</a>')
            cursor.setPosition(new_cursor_position)
            self.text_edit.setTextCursor(cursor)

            # Fetch the current links from the database
            links_data = supabase.table('docs').select('links').eq('doc_id', docId).execute().data
            current_links = links_data[0]['links'] if links_data else {}

            # Update the link for the original text
            current_links[original_text] = link

            # Update the links column in the database
            supabase.table('docs').update({'links': current_links}).eq('doc_id', docId).execute()

            # Close the dialog
            dialog.accept()
        except Exception as e:
            print(f"An error occurred during update_link: {e}")

    def fetch_clickable_links(self):
        try:
            # Fetch the clickable links from the database
            links_data = supabase.table('docs').select('links').eq('doc_id', docId).execute().data
            clickable_links = links_data[0]['links'] if links_data else {}

            # Display the links in a QTextBrowser
            links_browser = QTextBrowser()
            for original_text, link in clickable_links.items():
                links_browser.append(f'<a href="{link}">{original_text}</a>')
                
            links_browser.anchorClicked.connect(self.handle_link_click)

            # Create a pop-up dialog to display the links
            dialog = QDialog(self)
            dialog.setWindowTitle("Your Links")
            layout = QVBoxLayout()
            layout.addWidget(links_browser)
            dialog.setLayout(layout)

            # Show the dialog
            dialog.exec_()
        except Exception as e:
            print(f"An error occurred during fetch_clickable_links: {e}")
            
    def handle_link_click(self, link):
    # Open the clicked link in the default web browser
        QDesktopServices.openUrl(QUrl(link.url()))

    def text_edit_changed(self):
        try:
            # Fetch the current links from the database
            links_data = supabase.table('docs').select('links').eq('doc_id', docId).execute().data
            current_links = links_data[0]['links'] if links_data else {}

            # Check if any original text in the QTextEdit has been removed
            for original_text in list(current_links.keys()):
                if original_text not in self.text_edit.toPlainText():
                    del current_links[original_text]

            # Update the links column in the database
            supabase.table('docs').update({'links': current_links}).eq('doc_id', docId).execute()
        except Exception as e:
            print(f"An error occurred during text_edit_changed: {e}")

    def fetch_and_update_content(self):

        try:
            # Disconnect the textChanged signal temporarily
            self.text_edit.textChanged.disconnect(self.text_edit.send_data)
            cursor_position = self.text_edit.textCursor().position()
            # self.update_ui()
            # self.update_text_edit()
            # Fetch the latest content based on the doc_id
            doc_query = supabase.table('docs').select('content', 'access').eq('doc_id', docId).execute()
            user_uuids = supabase.table('docs').select('users').eq('doc_id', docId).execute().data[0]['users']  
            if doc_query and doc_query.data:
                latest_content = doc_query.data[0]['content']
                access_level = doc_query.data[0]['access']
                
                # Update the text_edit only if the content or access level has changed
                if latest_content != self.text_edit.toHtml():
                    cursor = self.text_edit.textCursor()
                    cursor.setPosition(cursor_position)
                    self.text_edit.setText(latest_content)
                    # print("Content updated.")

                # Check if access level is updated
                if access_level != None:
                    if access_level == "Restricted":
                        icon = QIcon("resources/images/lock.png")
                        self.navbar.pushButton_6.setIcon(icon)
                    elif access_level == "Readable":
                        icon = QIcon("resources/images/read.png")
                        self.navbar.pushButton_6.setIcon(icon)
                    else:
                        icon = QIcon("resources/images/write.png")
                        self.navbar.pushButton_6.setIcon(icon)
                        
                user_uuids = supabase.table('docs').select('users').eq('doc_id', docId).execute().data[0]['users']
                
            user_uuids = supabase.table('docs').select('users').eq('doc_id', docId).execute().data[0]['users']
            
            if (userId in user_uuids):
                if userId == user_uuids[0]:
                    self.text_edit.setReadOnly(False)
                    self.navbar.menuBar().setEnabled(True)
                    self.navbar.menuBar().findChild(QMenu, "menuAccess").setEnabled(True)
                else:
                    user_access = supabase.table('docs').select('user_access').eq('doc_id', docId).execute().data[0]['user_access']
                    access_type = user_access[userId]    
                    if access_type == "Restricted":
                        if userId: user_uuids.remove(userId)
                        supabase.table('docs').update({'users': user_uuids}).eq('doc_id', docId).execute()
                        self.switch_to_home()
                        self.switch_to_home()
                    elif access_type == "Reader":
                        self.text_edit.setReadOnly(True)
                    elif access_type == "Writer":
                        self.text_edit.setReadOnly(False)
                        
                    self.navbar.menuBar().findChild(QMenu, "menuAccess").setEnabled(False)
                    
               
            else:
                access_type = supabase.table('docs').select('access').eq('doc_id', docId).execute().data[0]['access']
                if access_type == "Restricted":
                    self.switch_to_home()
                if access_type == "Readable":
                    self.navbar.menuBar().findChild(QMenu, "menuAccess").setEnabled(False)
                    self.text_edit.setReadOnly(True)
                else:
                    self.navbar.menuBar().findChild(QMenu, "menuAccess").setEnabled(False)
                    self.text_edit.setReadOnly(False)
                        
                    
            # Reconnect the textChanged signal
            self.text_edit.textChanged.connect(self.text_edit.send_data)        
        except Exception as e:
            print(f"An error occurred during fetch_and_update_content: {e}")

    def update_share_button(self, access_type):
        if access_type == 'read' and not hasattr(self, 'read_button_updated'):
            self.navbar.pushButtonShare.setEnabled(True)
            self.navbar.pushButtonShare.clicked.connect(lambda: self.generate_general_access_link(docId, 'read'))
            self.read_button_updated = True
        elif access_type == 'write' and not hasattr(self, 'write_button_updated'):
            self.navbar.pushButtonShare.setEnabled(True)
            self.navbar.pushButtonShare.clicked.connect(lambda: self.generate_general_access_link(docId, 'write'))
            self.write_button_updated = True
    def start_sync_timer(self):
        # Set up a QTimer to periodically fetch and update content
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.fetch_and_update_content)
        self.sync_timer.start(25)  # Adjust the interval as needed (in milliseconds)
        print("Sync timer started.")

    def update_text_edit(self):
        try:
            # Fetch initial content from Supabase 'docs' table
            user_uuids = supabase.table('docs').select('users').eq('doc_id', docId).execute().data[0]['users']
            if (userId in user_uuids):
                if userId == user_uuids[0]:
                    initial_data = supabase.table('docs').select('content').eq('doc_id', docId).execute().data[0]['content']
                    print("\nInitial data: \n", initial_data)
                    self.text_edit.setText(initial_data)
                    self.text_edit.setReadOnly(False)
                    self.navbar.menuBar().setEnabled(True)
                    self.navbar.menuBar().findChild(QMenu, "menuAccess").setEnabled(True)
                else:
                    user_access = supabase.table('docs').select('user_access').eq('doc_id', docId).execute().data[0]['user_access']
                    access_type = user_access[userId]    
                    if access_type == "Restricted":
                        AuthenticationManager.show_popup("Restricted Access", "You do not have access to this document.")
                        if userId: user_uuids.remove(userId)
                        supabase.table('docs').update({'users': user_uuids}).eq('doc_id', docId).execute()
                        # dict(user_access).pop(userId)
                        # supabase.table('docs').update({'user_access': user_access}).eq('doc_id', docId).execute()
                        self.switch_to_home()
                    elif access_type == "Reader":
                        self.text_edit.setReadOnly(True)
                        AuthenticationManager.show_popup("Read Only", "You have read access to this document.")     
                    elif access_type == "Writer":
                        self.text_edit.setReadOnly(False)
                        AuthenticationManager.show_popup("Write Access", "You have write access to this document.")
                        
                    # self.navbar.menuBar().setEnabled(False)
                    self.navbar.menuBar().findChild(QMenu, "menuAccess").setEnabled(False)
                    
                
            else:
                access_type = supabase.table('docs').select('access').eq('doc_id', docId).execute().data[0]['access']
                if access_type == "Restricted":
                    AuthenticationManager.show_popup("Restricted Access", "You do not have access to this document.")
                    self.switch_to_home()
                if access_type == "Readable":
                    initial_data = supabase.table('docs').select('content').eq('doc_id', docId).execute().data[0]['content']
                    print("\nInitial data: \n", initial_data)
                    self.text_edit.setText(initial_data)
                    # self.navbar.menuBar().setEnabled(False)
                    self.navbar.menuBar().findChild(QMenu, "menuAccess").setEnabled(False)
                    self.text_edit.setReadOnly(True)
                    AuthenticationManager.show_popup("Read Only", "You have read access to this document.")
                else:
                    initial_data = supabase.table('docs').select('content').eq('doc_id', docId).execute().data[0]['content']
                    print("\nInitial data: \n", initial_data)
                    self.text_edit.setText(initial_data)
                    # self.navbar.menuBar().setEnabled(False)
                    self.navbar.menuBar().findChild(QMenu, "menuAccess").setEnabled(False)
                    self.text_edit.setReadOnly(False)
                    AuthenticationManager.show_popup("Write Access", "You have write access to this document.")
                    
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
    def generate_general_access_link(self, doc_id, access_type):
        base_url = "https://docify.com/document/"
        access_link = f"{base_url}{doc_id}/{access_type}"
        return access_link
        # AuthenticationManager.show_popup("Access Link", f"Share this link with others to give them {access_type} access: {access_link}")
    def copy_access_link(self):
        # Call the generate_access_link method with doc_id and access_type
        # doc_id = "your_generated_doc_id"  # Replace with your actual doc_id retrieval logic
        # access_type = "read"  # or "write" depending on your use case
        access_type = supabase.table('docs').select('access').eq('doc_id', docId).execute().data[0]['access']
        if access_type == "Readable":
            access_type = "read"
        else :
            access_type = "write"
        access_link = MainWindow.generate_general_access_link(self, docId, access_type)

        # Copy the access link to the clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(access_link)

        # Show a confirmation message
        AuthenticationManager.show_popup("URL Copied", "The access link has been copied to the clipboard.")
    
    def handle_access_link(self):
        try:
            # Parse the URL to extract information (doc_id and access_type)
            url = self.home_page.lineEditAccess.text()
            # parsed_url = url.toString()
            path_segments = url.split("/")
            doc_id = path_segments[4] if len(path_segments) > 3 else None
            
            doc_name = supabase.table('docs').select('name').eq('doc_id', doc_id).execute().data[0]['name']
            
            if doc_id:
                self.open_doc(doc_name)
            else: 
                AuthenticationManager.show_popup("Invalid URL", "The URL you entered is invalid")
            # access_type = path_segments[3] if len(path_segments) > 3 else None

            # if doc_id and access_type:
            #     # Implement logic to handle opening the document based on doc_id and access_type
            #     if access_type == "read":
            #         self.open_document(doc_id, read_only=True)
            #     elif access_type == "write":
            #         self.open_document(doc_id, read_only=False)

        except Exception as e:
            AuthenticationManager.show_popup("Invalid URL", "The document you are trying to access does not exist.")
            print(f"An error occurred during handle_access_link: {e}")
        
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
            self.update_ui()
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
    def create_doc_widget(self, doc_name):
        # Create a frame to encapsulate each document's information
        doc_frame = QFrame()
        doc_frame.setStyleSheet("background-color: white; border-radius: 10px;")  # Set background color and rounded corners
        doc_frame.setFixedHeight(300)  # Set a larger fixed height for the frame
        doc_frame.setFixedWidth(220)
        # Create a button for the document
        doc_button = QPushButton(doc_name)
        doc_button.setStyleSheet("background-color: #32CC70; border-radius: 20px;")  
        doc_button.setFixedHeight(50)# Set background color and rounded corners
        doc_button.clicked.connect(lambda _, name=doc_name: self.open_doc(name))

        # Set up a vertical layout for the frame and add the button
        frame_layout = QVBoxLayout()

        # Add a QLabel displaying the "DOC" image in the center of the box
        doc_label = QLabel()
        pixmap = QPixmap("resources/images/docs.png")
        doc_label.setPixmap(pixmap)
        doc_label.setFixedHeight(150)
        doc_label.setScaledContents(True)
        doc_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(doc_label)

        # Add spacing for better visual separation
        frame_layout.addSpacing(10)

        frame_layout.addWidget(doc_button)
        doc_frame.setLayout(frame_layout)

        return doc_frame

    def open_doc(self, doc_name) :
        global docId
        docId = supabase.table('docs').select('doc_id').eq('name', doc_name).execute().data[0]['doc_id']
        access_type = supabase.table('docs').select('access').eq('doc_id', docId).execute().data[0]['access']
        user_access = supabase.table('docs').select('user_access').eq('doc_id', docId).execute().data[0]['user_access']
        user_uuids = supabase.table('docs').select('users').eq('doc_id', docId).execute().data[0]['users']
        if (userId!=user_uuids[0] and access_type == "Restricted") and (user_access[userId]=="Restricted"):
            AuthenticationManager.show_popup("Restricted Access", "You do not have access to this document.")
        else:
            self.switch_to_navbar(doc_name)
        
    def switch_to_navbar(self, doc_name):

        # Switch to the home page
        self.stacked_widget.setCurrentIndex(3)
        self.navbar.pushButton_6.setText(f"{doc_name}")
        self.navbar.label.setText(f"Hi {username}!")
        # access_type = supabase.table('docs').select('access').eq('doc_id', docId).execute().data[0]['access']
        # if access_type == "Restricted":
        #     icon = QIcon("resources/images/lock.png")
        global docName
        docName = doc_name
        self.update_text_edit()

        # Connect the textChanged signal to the send_data method
        if not hasattr(self.text_edit, 'connected'):
            # Connect the textChanged signal to the send_data method
            self.text_edit.textChanged.connect(self.text_edit.send_data)
            # Mark the connection as established
            self.text_edit.connected = True
    def open_share_dialog(self, doc_name):
        share_dialog = ShareDialog(doc_name)
        userIds = supabase.table('docs').select('users').eq('doc_id', docId).execute().data[0]['users']
        if userId != userIds[0]:
            share_dialog.lineEdit.setPlaceholderText("You are not the owner")
            share_dialog.lineEdit.setEnabled(False)
            share_dialog.comboBox.setEnabled(False)
            share_dialog.pushButtonDone.setEnabled(False)
            # share_dialog.pushButtonCopy.setEnabled(False)
            # share_dialog.pushButtonCopy.setText("Restricted")
        share_dialog.exec_()
    def update_access(self, access_level):
        try:
            # Fetch the doc_id based on the current document name
            doc_id = supabase.table('docs').select('doc_id').eq('name', self.navbar.pushButton_6.text()).execute().data[0]['doc_id']

            # Update the access column in the docs table
            supabase.table('docs').update({'access': access_level}).eq('doc_id', doc_id).execute()

            # Show a popup confirming the update
            AuthenticationManager.show_popup("Access Level Updated", f"Access level updated to {access_level}")

        except Exception as e:
            print(f"An error occurred during update_access: {e}")
            # Show a popup with the error message
            AuthenticationManager.show_popup("Error", f"An error occurred: {e}") 
    def refresh(self):
        self.update_ui()
        self.update_text_edit()  
    def listen_for_changes(self):
        try:
            while True:
                # Receive data from the server
                data = self.server_socket.recv(1024)
                if not data:
                    break

            # Update the textEdit in the navbar with the received data
            received_text = data.decode('utf-8')
            self.text_edit.setText(received_text)               

        except Exception as e:
            print(f"An error occurred during listen_for_changes: {e}")
            
    def convert_to_pdf(self):
        try: 
            # Get the text document from the text edit
            text_content = self.text_edit.toHtml()

            text_document = QTextDocument()
            text_document.setHtml(text_content)

            # Get the document name from Supabase
            doc_name = supabase.table('docs').select('name').eq('doc_id', docId).execute().data[0]['name']

            # Determine the 'Documents' folder in 'Docify'
            documents_folder = os.path.join(os.path.expanduser("~"), "Desktop", "Docify", "Documents")
            os.makedirs(documents_folder, exist_ok=True)

            # Set up the PDF file name
            pdf_file_path = os.path.join(documents_folder, f"{doc_name}.pdf")

            # Set up the QPrinter
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(pdf_file_path)

            # Use the QPrinter to generate the PDF
            text_document.print_(printer)
            AuthenticationManager.show_popup("PDF Saved", f"PDF saved successfully at: {pdf_file_path}")
        except Exception as e:
            AuthenticationManager.show_popup("Failed", f"Conversion to PDF failed due to {e}")

            
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
            
    def logout(self):
        # response = self.auth_manager.logout()

        # if response:
        self.switch_to_login()
        self.stacked_widget.setCurrentIndex(0)
            
    def signinGoogle(self):
        response = self.auth_manager.signinWithGoogle()

        if response:
            print(response)
            self.switch_to_home()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec_()
    