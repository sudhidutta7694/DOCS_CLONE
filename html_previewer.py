import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.uic import *
from cloudinary_credentials import *
from credentials import *
import cloudinary.uploader
import os, requests

class ImageObject(QTextObjectInterface):
    def __init__(self, parent):
        super().__init__(parent)

    def intrinsicSize(self, format, doc, cursor):
        width = format.property("width").toInt()[0]
        height = format.property("height").toInt()[0]
        return QSizeF(width, height)

    def drawObject(self, painter, rect, doc, cursor, format):
        image_path = format.property("imagePath")
        pixmap = QPixmap(image_path)

        painter.drawPixmap(rect, pixmap)

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

class HtmlGenerator(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_html)
        self.timer.start(25)

    def init_ui(self):
        self.setWindowTitle('HTML Generator')
        self.setGeometry(100, 100, 800, 600)

        self.text_edit = QTextEdit(self)
        self.html_preview = QTextEdit(self)
        self.html_preview.setReadOnly(True)

        self.add_image_btn = QPushButton('Add Image', self)
        self.bold_btn = QPushButton('Bold', self)
        self.italic_btn = QPushButton('Italic', self)
        self.underline_btn = QPushButton('Underline', self)
        self.font_size_btn = QPushButton('Text Size', self)
        self.font_color_btn = QPushButton('Font Color', self)

        self.setup_layout()

        self.add_image_btn.clicked.connect(self.add_image)
        self.bold_btn.clicked.connect(self.toggle_bold)
        self.italic_btn.clicked.connect(self.toggle_italic)
        self.underline_btn.clicked.connect(self.toggle_underline)
        self.font_size_btn.clicked.connect(self.set_font_size)
        self.font_color_btn.clicked.connect(self.set_font_color)

        self.show()

    def setup_layout(self):
        main_layout = QVBoxLayout(self)

        main_layout.addWidget(self.text_edit)
        main_layout.addWidget(self.html_preview)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_image_btn)
        button_layout.addWidget(self.bold_btn)
        button_layout.addWidget(self.italic_btn)
        button_layout.addWidget(self.underline_btn)
        button_layout.addWidget(self.font_size_btn)
        button_layout.addWidget(self.font_color_btn)

        main_layout.addLayout(button_layout)

    # def add_image(self):
    #     file_dialog = QFileDialog()
    #     image_path, _ = file_dialog.getOpenFileName(self, 'Select Image', '', 'Images (*.png *.xpm *.jpg *.bmp)')

    #     if image_path:
    #         size_dialog = ImageSizeDialog(self)
    #         width, height = size_dialog.get_image_size()

    #         if width is not None and height is not None:
    #             image_format = QTextImageFormat()
    #             image_format.setName(image_path)
    #             image_format.setWidth(width)
    #             image_format.setHeight(height)

    #             cursor = self.text_edit.textCursor()
    #             cursor.insertImage(image_format)
    
    def add_image(self):
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(self, 'Select Image', '', 'Images (*.png *.xpm *.jpg *.bmp)')

        if image_path:
            size_dialog = ImageSizeDialog(self)
            width, height = size_dialog.get_image_size()

            if width is not None and height is not None:
                image_name = image_path.split('/')[-1][:-4]
                upload_result = cloudinary.uploader.upload(image_path, public_id = image_name)
                
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

                    cursor = self.text_edit.textCursor()
                    cursor.insertImage(image_format)
                    self.update_html()  # Assuming you have an update_html function to refresh the preview
    # def add_image(self):
    #     file_dialog = QFileDialog()
    #     image_path, _ = file_dialog.getOpenFileName(self, 'Select Image', '', 'Images (*.png *.xpm *.jpg *.bmp)')

    #     if image_path:
    #         size_dialog = ImageSizeDialog(self)
    #         width, height = size_dialog.get_image_size()

    #         if width is not None and height is not None:
    #             image_name = image_path.split('/')[-1]
    #             upload_result = cloudinary.uploader.upload(image_path, public_id=image_name)

    #             if 'secure_url' in upload_result:
    #                 hosted_url = upload_result['secure_url']
    #                 print("Hosted image URL:", hosted_url)

    #                 # Download the image to a local directory
    #                 local_directory = '/home/sudhi-sundar-dutta/Desktop/Docify/images'
    #                 local_path = os.path.join(local_directory, image_name)

    #                 response = requests.get(hosted_url, stream=True)
    #                 with open(local_path, 'wb') as file:
    #                     for chunk in response.iter_content(chunk_size=128):
    #                         file.write(chunk)

    #                 # Construct the HTML img tag with the local path
    #                 img_tag = f'<img src="{local_path}" width="{width}" height="{height}">'

    #                 # Get the current cursor position
    #                 cursor = self.text_edit.textCursor()
    #                 position = cursor.position()

    #                 # Insert the HTML img tag at the cursor position
    #                 cursor.insertHtml(img_tag)

    #                 # Set the cursor position after the inserted image
    #                 cursor.setPosition(position + len(img_tag))

    #                 # Refresh the HTML preview
    #                 self.update_html()
                    
    def toggle_bold(self):
        self.toggle_format(QTextCharFormat.FontWeight)

    def toggle_italic(self):
        self.toggle_format(QTextCharFormat.FontItalic)

    def toggle_underline(self):
        self.toggle_format(QTextCharFormat.FontUnderline)

    def toggle_format(self, format_flag):
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        current_value = char_format.property(format_flag)

        char_format.setProperty(format_flag, not current_value)
        cursor.mergeCharFormat(char_format)

    def set_font_size(self):
        cursor = self.text_edit.textCursor()
        current_size = cursor.charFormat().fontPointSize()
        new_size, ok = QInputDialog.getInt(self, 'Text Size', 'Enter text size:', current_size)

        if ok:
            self.text_edit.setFontPointSize(new_size)

    def set_font_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_edit.setTextColor(color)

    def update_html(self):
        html = self.text_edit.toHtml()
        self.html_preview.setHtml(html)

        with open('output.html', 'w') as file:
            file.write(html)

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         self.init_ui()

#     def init_ui(self):
#         central_widget = loadUi('./ui/nav.ui')  # Replace 'path/to/nav.ui' with the actual path
#         self.setCentralWidget(central_widget)

#         # Find widgets in nav.ui by their object names and connect them to your existing functions
#         central_widget.findChild(QPushButton, 'addImageBtn').clicked.connect(HtmlGenerator.add_image)
#         central_widget.findChild(QPushButton, 'boldBtn').clicked.connect(HtmlGenerator.toggle_bold)
#         central_widget.findChild(QPushButton, 'italicBtn').clicked.connect(HtmlGenerator.toggle_italic)
#         central_widget.findChild(QPushButton, 'underlineBtn').clicked.connect(HtmlGenerator.toggle_underline)
#         central_widget.findChild(QPushButton, 'fontSizeBtn').clicked.connect(HtmlGenerator.set_font_size)
#         central_widget.findChild(QPushButton, 'fontColorBtn').clicked.connect(HtmlGenerator.set_font_color)

#         layout = QVBoxLayout(central_widget)
#         html_generator = HtmlGenerator()
#         layout.addWidget(html_generator)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HtmlGenerator()
    sys.exit(app.exec_())
