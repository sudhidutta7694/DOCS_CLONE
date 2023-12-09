from utils.constants import *
from utils.supabase_client import supabase

import webbrowser
import bcrypt
from PyQt5.QtWidgets import QMessageBox

class AuthenticationManager:
    @staticmethod
    def hash_password(password):
    # Generate a random salt using the secrets module
        salt = bcrypt.gensalt()

    # Hash the password using bcrypt and the generated salt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

        return hashed_password
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
                    'password':  AuthenticationManager.hash_password(password).decode('utf-8')  # Note: Make sure to hash the password before storing it
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
                