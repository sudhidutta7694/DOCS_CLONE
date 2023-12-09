from utils.constants import *
from utils.supabase_client import supabase

from PyQt5.QtWidgets import QTextEdit

class MyTextEdit(QTextEdit):
    def __init__(self, server_socket):
        super().__init__()

        self.server_socket = server_socket

        self.textChanged.connect(self.send_data)

    def send_data(self):
        text = self.toPlainText()
        print(f"User Id: {userId}")
        # Check if docId is initialized
        if docId is None and userId is not None:
            # Use Supabase query to get the doc_id where the users array contains the logged-in user ID
            doc_id_query = supabase.table('docs').select('doc_id').contains('users', [userId]).execute()

            # Assuming the result is a list of rows, get the doc_id from the first row (if available)
            if doc_id_query and doc_id_query.data:
                doc_id = doc_id_query.data[0]['doc_id']
                global docId2
                docId2 = doc_id
                # print(f"Doc ID for the logged-in user: {doc_id}")
                supabase.table('docs').update({'content': text}).eq('doc_id', docId2).execute()
                self.server_socket.sendall(text.encode())
                
            else:
                print("No matching document found for the logged-in user.")
        elif (docId is not None and userId is not None):
            supabase.table('docs').update({'content': text}).eq('doc_id', docId).execute()
            self.server_socket.sendall(text.encode())
