from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt5.uic import loadUi
from supabase import create_client
import webbrowser
from credentials import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


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
            response = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password,
            })

            if response:
                AuthenticationManager.show_popup("User Already Exists",
                                                 "This user is already registered.")
                # Redirect to the login page or perform any other action as needed
                stacked_widget.setCurrentIndex(0)
            else:
                response = supabase.auth.sign_up({
                    'email': email,
                    'password': password,
                    'options': {
                        'data': {
                            'name': full_name
                        }
                    }
                })

            print("Signup successful!")
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
            return response

        except Exception as e:
            print(f"An error occurred during login: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Create a stacked widget
        self.stacked_widget = QStackedWidget()

        # Load the login and signup pages from their respective UI files
        self.login_page = loadUi('ui/login.ui')
        self.signup_page = loadUi('ui/signup.ui')
        self.home_page = loadUi('ui/home.ui')

        # Add the pages to the stacked widget
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.signup_page)
        self.stacked_widget.addWidget(self.home_page)

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

    def switch_to_home(self, response):
        # Switch to the home page
        self.stacked_widget.setCurrentIndex(2)
        # user_name = response.user.user_metadata.get('name').split(" ")[0]
        # self.home_page.welcome_label.setText(f"Hi {user_name}!")

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
            self.switch_to_home(response)

    def login(self):
        email = self.login_page.lineEditEmail.text()
        password = self.login_page.lineEditPassword.text()

        response = self.auth_manager.login(email, password)

        if response:
            self.switch_to_home(response)
            
    def signinGoogle(self):
        # email = self.login_page.lineEditEmail.text()
        # password = self.login_page.lineEditPassword.text()

        response = self.auth_manager.signinWithGoogle()

        if response:
            print(response)
            self.switch_to_home(response)


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
