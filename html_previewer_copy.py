import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi  # Import the loadUi function to load the .ui file

from cloudinary_credentials import *
from credentials import *
import cloudinary.uploader
import os
import requests

# class ImageObject(QTextObjectInterface):
#     def __init__(self, parent):
#         super().__init__(parent)

#     def intrinsicSize(self, format, doc, cursor):
#         width = format.property("width").toInt()[0]
#         height = format.property("height").toInt()[0]
#         return QSizeF(width, height)

#     def drawObject(self, painter, rect, doc, cursor, format):
#         image_path = format.property("imagePath")
#         pixmap = QPixmap(image_path)

#         painter.drawPixmap(rect, pixmap)
class LinkDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.name_label = QLabel("Name:")
        self.link_label = QLabel("Link:")
        self.name_line_edit = QLineEdit()
        self.link_line_edit = QLineEdit()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_line_edit)
        layout.addWidget(self.link_label)
        layout.addWidget(self.link_line_edit)
        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.setLayout(layout)
        
    def get_link_info(self):
        result = self.exec_()
        if result == QDialog.Accepted:
            name = self.name_line_edit.text()
            link = self.link_line_edit.text()
            return name, link
        else:
            return None, None

class ImageSizeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.width_label = QLabel("Width:")
        self.height_label = QLabel("Height:")
        self.width_spinbox = QSpinBox()
        self.height_spinbox = QSpinBox()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.width_label)
        layout.addWidget(self.width_spinbox)
        layout.addWidget(self.height_label)
        layout.addWidget(self.height_spinbox)
        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.setLayout(layout)

    def get_image_size(self):
        result = self.exec_()
        if result == QDialog.Accepted:
            return self.width_spinbox.value(), self.height_spinbox.value()
        else:
            return None, None

class HtmlGenerator(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load the UI from nav.ui
        loadUi('./ui/navbar.ui', self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_html)
        self.timer.start(25)
        
        self.actionTable.triggered.connect(self.add_link)
        self.actionImage.triggered.connect(self.add_image)
        self.pushButton.clicked.connect(self.toggle_bold)
        self.pushButton_2.clicked.connect(self.toggle_italic)
        self.pushButton_3.clicked.connect(self.toggle_underline)
        # self.font_size_btn.clicked.connect(self.set_font_size)
        self.pushButtonColour.clicked.connect(self.set_font_color)
        
        self.link_display = QTextBrowser()
        self.link_display.setOpenExternalLinks(True)  # Enable opening external links

        layout = QVBoxLayout(self.centralWidget())
        layout.addWidget(self.textEdit)
        layout.addWidget(self.link_display)

    def add_image(self):
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(self, 'Select Image', '', 'Images (*.png *.xpm *.jpg *.bmp)')

        if image_path:
            size_dialog = ImageSizeDialog(self)
            width, height = size_dialog.get_image_size()

            if width is not None and height is not None:
                image_name = image_path.split('/')[-1][:-4]
                upload_result = cloudinary.uploader.upload(image_path, public_id=image_name)
                
                if 'secure_url' in upload_result:
                    hosted_url = upload_result['secure_url']
                    print("Hosted image URL:", hosted_url)

                    # Download the image to a local directory
                    local_directory = '/home/sudhi-sundar-dutta/Desktop/Docify/images'
                    local_path = os.path.join(local_directory, image_name)

                    response = requests.get(hosted_url, stream=True)
                    with open(local_path, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=128):
                            file.write(chunk)

                    # Insert the hosted image URL into the QTextEdit
                    image_format = QTextImageFormat()
                    image_format.setWidth(width)
                    image_format.setHeight(height)
                    image_format.setName(local_path)

                    cursor = self.textEdit.textCursor()
                    cursor.insertImage(image_format)
                    self.update_html()
    def add_link(self):
        link_dialog = LinkDialog(self)
        name, link = link_dialog.get_link_info()

        if name and link:
            # Insert the link into the QTextEdit
            link_html = f'<a href="{link}">{name}</a>'
            cursor = self.textEdit.textCursor()
            cursor.insertHtml(link_html)
            self.update_html()

            # Add the link to the displayed clickable links
            self.link_display.append(f'<a href="{link}">{name}</a>')
    def toggle_bold(self):
        self.toggle_format(QTextCharFormat.FontWeight)

    def toggle_italic(self):
        self.toggle_format(QTextCharFormat.FontItalic)

    def toggle_underline(self):
        self.toggle_format(QTextCharFormat.FontUnderline)

    def toggle_format(self, format_flag):
        cursor = self.textEdit.textCursor()
        char_format = cursor.charFormat()
        current_value = char_format.property(format_flag)

        char_format.setProperty(format_flag, not current_value)
        cursor.mergeCharFormat(char_format)

    def set_font_size(self):
        cursor = self.textEdit.textCursor()
        current_size = cursor.charFormat().fontPointSize()
        new_size, ok = QInputDialog.getInt(self, 'Text Size', 'Enter text size:', current_size)

        if ok:
            self.textEdit.setFontPointSize(new_size)

    def set_font_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.textEdit.setTextColor(color)

    def update_html(self):
        html = self.textEdit.toHtml()
        # self.html_preview.setHtml(html)

        with open('output.html', 'w') as file:
            file.write(html)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        html_generator = HtmlGenerator()
        layout.addWidget(html_generator)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HtmlGenerator()
    window.show()
    sys.exit(app.exec_())
