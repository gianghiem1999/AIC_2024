import socketio
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QFileDialog, QMessageBox, QDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLineEdit
from PyQt5.QtGui import QPixmap
from googletrans import Translator
import spacy
from functools import partial
import os
import csv
import subprocess
import platform
import zipfile

# Lưu tin nhắn từ server
result_json = {}

# Khởi tạo client SocketIO
sio = socketio.Client()

# Xử lý sự kiện khi kết nối thành công
@sio.event
def connect():
    print("Đã kết nối với server")

# Xử lý sự kiện khi ngắt kết nối
@sio.event
def disconnect():
    print("Đã ngắt kết nối với server")

# Xử lý sự kiện khi nhận kết quả từ server
@sio.event
def result(data):
    global result_json
    result_json = data
    for json_key, json_value in data.items():
        print(f"{json_key}: {json_value}")
    
    # Tạo cửa sổ kết quả sau khi nhận phản hồi từ server
    num, lett, char = app.extract_phrases(app.translated_text)  # Xử lý các số, chữ cái và ký tự đặc biệt
    app.show_result_signal.emit(app.translated_text, num, lett, char)  # Phát tín hiệu để mở cửa sổ phụ

# Kết nối đến server
server_url = 'http://localhost:5000'  # Địa chỉ và cổng của server
sio.connect(server_url)

# Load the English model
nlp = spacy.load('en_core_web_sm')

class ZoomedImageWidget(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        self.image_label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # pixmap = pixmap.scaledToWidth(1000, Qt.SmoothTransformation)  # Resize ảnh khi phóng to
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Image not found")
        
        layout.addWidget(self.image_label)
        self.adjustSize()  # Adjust the size of the widget to fit the image
        # self.setWindowOpacity(0.9)  # Optional: Set opacity for better visibility

class HoverableThumbnail(QLabel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.default_pixmap = QPixmap(self.image_path)
        self.zoomed_image_widget = None
        self.original_pixmap = None
        
        # Thiết lập kích thước mặc định
        self.set_thumbnail_size(350)
        
    def set_thumbnail_size(self, width):
        if not self.default_pixmap.isNull():
            # Scale ảnh về kích thước width, giữ tỷ lệ chiều cao
            pixmap = self.default_pixmap.scaledToWidth(width, Qt.SmoothTransformation)
            self.setPixmap(pixmap)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.zoomed_image_widget is None:
                self.original_pixmap = self.pixmap()  # Lưu ảnh gốc
                self.zoomed_image_widget = ZoomedImageWidget(self.image_path)
                self.zoomed_image_widget.show()  # Hiển thị widget phóng to
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.zoomed_image_widget is not None:
                self.zoomed_image_widget.close()  # Đóng widget phóng to
                self.zoomed_image_widget = None
                self.setPixmap(self.original_pixmap)  # Khôi phục kích thước ảnh gốc
        super().mouseReleaseEvent(event)


class ResultWindow(QWidget):
    def __init__(self, translated_text, num, lett, char):
        super().__init__()
        self.setWindowTitle("Results")
        self.setGeometry(100, 100, 1670, 850)
        self.num_results = len(result_json)
        self.num_selections ={}
        self.layout1 = QVBoxLayout()
        # self.layout2 = QHBoxLayout()
        # self.layout2a = QVBoxLayout()
        # self.layout2b = QVBoxLayout()
        # self.layout3 = QHBoxLayout()
        # self.layout3a = QVBoxLayout()
        # self.layout3b = QVBoxLayout()
        self.layout4 = QHBoxLayout()
        # self.layout4a = QVBoxLayout()
        self.layout4b = QVBoxLayout()
        self.layout5 = QHBoxLayout()
        self.layout5a = QVBoxLayout()
        self.layout5b = QVBoxLayout()
        self.layout6 = QVBoxLayout()    
        self.layout7 = QHBoxLayout()
        self.layout8 = QVBoxLayout()
        self.layout9 = QVBoxLayout()

        self.layout_main1 = QVBoxLayout()
        self.layout_main2 = QVBoxLayout()
        self.layout_main3 = QVBoxLayout()
        self.layout_main = QHBoxLayout()


        # Add labels and set text

        self.output_label = QLabel("<b>Translated text:</b>")
        self.output_text = QLabel(translated_text)
        self.output_text.setWordWrap(True)
        self.output_text.setFixedWidth(350)

        self.num_label = QLabel("<b>Numbers:</b>")
        self.num_text = QLabel(', '.join(num))
        self.num_text.setWordWrap(True)
        self.num_text.setFixedWidth(350)

        self.lett_label = QLabel("<b>Letters:</b>")
        self.lett_text = QLabel(', '.join(lett))
        self.lett_text.setWordWrap(True)
        self.lett_text.setFixedWidth(150)

        self.char_label = QLabel("<b>Characters:</b>")
        self.char_text = QLabel(', '.join(char))
        self.char_text.setWordWrap(True)
        self.char_text.setFixedWidth(150)

        self.result_label = QLabel("<b>Priority Result</b>")
        # Example result entry (to be replaced with dynamic content)
        self.result_entries = QVBoxLayout()
        # self.result_showImage = [None]*(self.num_results + 1)
        self.result_select = [None]*(self.num_results + 1)
        self.result_name = [None]*(self.num_results + 1)
        self.result_frameID = [None]*(self.num_results + 1)

        for i, (json_key, json_value) in enumerate(result_json.items()):  # Lặp qua từng json_key, json_value
            result_entry = QHBoxLayout()

            # Hiển thị json_key tại phần result_no
            result_no = QLabel(f"{json_key}.")
            result_no.setFixedWidth(75)

            # Hiển thị value của sub_key "keyframe" cho mỗi json_key tại phần self.result_name
            keyframe_value = json_value.get("keyframe", "N/A")
            self.result_name[i + 1] = QLabel(f"{keyframe_value}")
            self.result_name[i + 1].setFixedWidth(80)

            # Hiển thị value của sub_key "frameid" cho mỗi json_key tại phần self.result_frameID
            frameid_value = json_value.get("frameid", "N/A")
            self.result_frameID[i + 1] = QLabel(f"{frameid_value}")
            self.result_frameID[i + 1].setFixedWidth(80)

            # Hiển thị thumbnails tương ứng.
            name_value = json_value.get("name", "N/A")
            if name_value != "N/A" and keyframe_value != "N/A":
                image_path = f"keyframes/{keyframe_value}/{name_value}"
                thumbnail = HoverableThumbnail(image_path)
            else:
                # Nếu không có ảnh, tạo QLabel mặc định
                thumbnail = QLabel(f"Image not available {i + 1}")
                thumbnail.setFixedWidth(350)  # Set a default width

            # self.result_showImage[i + 1] = QPushButton(f"Show Image {i + 1}")
            # # Kết nối nút với phương thức show_image, truyền vào đường dẫn ảnh
            # self.result_showImage[i + 1].clicked.connect(partial(self.show_image, image_path, keyframe_value, name_value, frameid_value))

            self.result_select[i + 1] = QPushButton(f"Select Image {name_value}")

            # Thêm các widget vào layout
            result_entry.addWidget(result_no)
            result_entry.addWidget(self.result_name[i + 1])
            result_entry.addWidget(self.result_frameID[i + 1])
            result_entry.addWidget(thumbnail)
            # result_entry.addWidget(self.result_showImage[i + 1])
            result_entry.addWidget(self.result_select[i + 1])

            # Thêm layout vào tổng layout
            self.result_entries.addLayout(result_entry)


        # Scroll area for results
        scroll_area = QScrollArea()
        scroll_area.setFixedWidth(815)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(self.result_entries)
        scroll_area.setWidget(scroll_content)

        self.selections_layout = QVBoxLayout()
        scroll_selections = QScrollArea()
        scroll_selections.setFixedWidth(495)
        scroll_selections.setWidgetResizable(True)
        scroll_selection_content = QWidget()
        scroll_selection_content.setLayout(self.selections_layout)
        scroll_selections.setWidget(scroll_selection_content)

        self.action = QPushButton("Add to CSV")
        self.check_csv = QPushButton("Check CSV")
        self.submit = QPushButton("Submit")

        self.selections = QLabel("<b>Selections</b>")


        # Add widgets to layout
        self.layout1.addWidget(self.output_label, alignment=Qt.AlignTop)
        self.layout1.addWidget(self.output_text, alignment=Qt.AlignTop)
        self.layout4b.addWidget(self.num_label, alignment=Qt.AlignTop)
        self.layout4b.addWidget(self.num_text, alignment=Qt.AlignTop)
        self.layout5a.addWidget(self.lett_label, alignment=Qt.AlignTop)
        self.layout5a.addWidget(self.lett_text, alignment=Qt.AlignTop)
        self.layout5b.addWidget(self.char_label, alignment=Qt.AlignTop)
        self.layout5b.addWidget(self.char_text, alignment=Qt.AlignTop)

        # self.layout2.addLayout(self.layout2a)
        # self.layout2.addLayout(self.layout2b)
        # self.layout3.addLayout(self.layout3a)
        # self.layout3.addLayout(self.layout3b)
        # self.layout4.addLayout(self.layout4a)
        self.layout4.addLayout(self.layout4b)
        self.layout4.setAlignment(self.layout4b, Qt.AlignTop)
        self.layout5.addLayout(self.layout5a)
        self.layout5.setAlignment(self.layout5a, Qt.AlignTop)
        self.layout5.addLayout(self.layout5b)
        self.layout5.setAlignment(self.layout5b, Qt.AlignTop)
        self.layout6.addWidget(self.result_label, alignment=Qt.AlignTop)
        self.layout6.addWidget(scroll_area)
        self.layout9.addWidget(self.action)
        self.layout7.addWidget(self.check_csv, alignment=Qt.AlignLeft)
        self.layout7.addWidget(self.submit, alignment=Qt.AlignRight)
        self.layout8.addWidget(self.selections, alignment=Qt.AlignTop)

        self.layout_main1.addLayout(self.layout1)
        self.layout_main1.setAlignment(self.layout1, Qt.AlignTop)
        # self.layout_main1.addLayout(self.layout2)
        # self.layout_main1.addLayout(self.layout3)
        self.layout_main1.addLayout(self.layout4)
        self.layout_main1.setAlignment(self.layout4, Qt.AlignTop)
        self.layout_main1.addLayout(self.layout5)
        self.layout_main1.setAlignment(self.layout5, Qt.AlignTop)
        self.layout_main2.addLayout(self.layout6)
        self.layout_main3.addLayout(self.layout8)
        self.layout_main3.addWidget(scroll_selections)
        self.layout_main3.addLayout(self.layout9)
        self.layout_main3.addLayout(self.layout7)

        self.layout_main.addLayout(self.layout_main1)
        self.layout_main.addLayout(self.layout_main2)
        self.layout_main.addLayout(self.layout_main3)

        self.setLayout(self.layout_main)

        # self.setLayout(self.layout)

        self.delete_option = [None]*(self.num_results + 1)
        self.selection = [None]*(self.num_results + 1)
        self.selected_frameID = [None]*(self.num_results + 1)
        self.answer = [None]*(self.num_results + 1)

        self.click_result_select()

        #export csv
        self.action.clicked.connect(self.save_to_csv)
        #check csv
        self.check_csv.clicked.connect(self.check_csv_file)
        #compress zip
        self.submit.clicked.connect(self.compress_csv_folder)

    def show_image(self, image_path, keyframe_value, name_value, frameid_value):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{keyframe_value} - {frameid_value} ({name_value})")
        layout = QVBoxLayout()

        image_label = QLabel()
        pixmap = QPixmap(image_path)

        if not pixmap.isNull():
            # pixmap = pixmap.scaledToWidth(600)  # Resize ảnh (tùy chỉnh kích thước hiển thị)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("Image not found")

        layout.addWidget(image_label)
        dialog.setLayout(layout)
        dialog.exec_()


    def process_result_select(self, i):
        key = self.result_name[i + 1].text()
        new_value = self.result_frameID[i + 1].text()

        # Kiểm tra xem giá trị mới đã tồn tại trong danh sách giá trị của key không
        if key in self.num_selections:
            if new_value in self.num_selections[key]:
                QMessageBox.warning(self, "Warning", "Image's already selected")
                return  # Dừng lại và không thêm vào layout_main3
            
            # Nếu key đã tồn tại nhưng giá trị mới khác giá trị cũ, append giá trị mới
            self.num_selections[key].append(new_value)
        else:
            # Nếu key chưa tồn tại, tạo danh sách giá trị với giá trị mới
            self.num_selections[key] = [new_value]

        # Tạo QHBoxLayout cho các lựa chọn
        self.choices = QHBoxLayout()
        
        self.selection[i + 1] = QLabel(self.result_name[i + 1].text())
        self.selection[i + 1].setFixedWidth(150)
        self.selected_frameID[i + 1] = QLabel(self.result_frameID[i + 1].text())
        self.selected_frameID[i + 1].setFixedWidth(100)
        self.answer[i + 1] = QLineEdit()
        self.answer[i + 1].setFixedWidth(125)
        self.delete_option[i + 1] = QPushButton("Delete")
        self.delete_option[i + 1].clicked.connect(partial(self.remove_selection, i + 1))  # Connect delete button

        # Thêm các widget vào QHBoxLayout
        self.choices.addWidget(self.selection[i + 1], alignment=Qt.AlignTop)
        self.choices.addWidget(self.selected_frameID[i + 1], alignment=Qt.AlignTop)
        self.choices.addWidget(self.answer[i + 1], alignment=Qt.AlignTop)
        self.choices.addWidget(self.delete_option[i + 1], alignment=Qt.AlignTop)  # Thêm nút xóa vào QHBoxLayout

        # Thêm QHBoxLayout vào layout_main3
        self.selections_layout.addLayout(self.choices)


    def remove_selection(self, index):
        # Xác định key và value cần xóa
        key_to_remove = self.selection[index].text()
        value_to_remove = self.selected_frameID[index].text()

        # Xóa giá trị khỏi dictionary
        if key_to_remove in self.num_selections:
            if value_to_remove in self.num_selections[key_to_remove]:
                self.num_selections[key_to_remove].remove(value_to_remove)
                
                # Nếu danh sách giá trị của key trở nên rỗng, xóa key
                if not self.num_selections[key_to_remove]:
                    del self.num_selections[key_to_remove]
                elif len(self.num_selections[key_to_remove]) == 0:
                    # Nếu danh sách giá trị chỉ còn một giá trị và giá trị đó là giá trị vừa xóa
                    if self.num_selections[key_to_remove][0] == value_to_remove:
                        del self.num_selections[key_to_remove]
                        
        # Xóa widget và layout
        item_to_remove = None
        for i in range(self.selections_layout.count()):
            layout_item = self.selections_layout.itemAt(i)
            if layout_item is not None:
                selection_layout = layout_item.layout()
                if selection_layout is not None:
                    frame_name_label = selection_layout.itemAt(0).widget()
                    if frame_name_label == self.selection[index]:
                        item_to_remove = layout_item
                        break

        if item_to_remove is not None:
            # Xóa các widget trong layout
            for j in reversed(range(item_to_remove.layout().count())):
                widget = item_to_remove.layout().itemAt(j).widget()
                if widget is not None:
                    widget.deleteLater()
            
            # Xóa layout item khỏi selections_layout
            self.selections_layout.removeItem(item_to_remove)
            
            # Xóa các tham chiếu
            self.selection[index] = None
            self.selected_frameID[index] = None
            self.answer[index] = None
            self.delete_option[index] = None


    def click_result_select(self):
        for i in range(self.num_results):
            self.result_select[i + 1].clicked.connect(partial(self.process_result_select, i))

    def save_to_csv(self):
        # Hỏi người dùng tên và vị trí tệp CSV
        options = QFileDialog.Options()
        csv_file, _ = QFileDialog.getSaveFileName(self, "Save to CSV", "csv_data/", "CSV Files (*.csv)", options=options)

        if csv_file:
            try:
                with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # writer.writerow(['Frame Name', 'FrameID'])  # Write the header

                    # Loop through selections_layout to get the selected frame names and FrameIDs
                    for i in range(self.selections_layout.count()):
                        layout_item = self.selections_layout.itemAt(i)
                        if layout_item is not None:
                            selection_layout = layout_item.layout()
                            if selection_layout is not None:
                                frame_name_label = selection_layout.itemAt(0).widget()
                                frameID_label = selection_layout.itemAt(1).widget()
                                answer_label = selection_layout.itemAt(2).widget()
                                if frame_name_label is not None and frameID_label is not None and (answer_label.text()).replace(" ", "") != "":
                                    writer.writerow([frame_name_label.text(), frameID_label.text(), f"{(answer_label.text()).replace(' ', '')}"])  #changed if contest's submission require changed
                                elif frame_name_label is not None and frameID_label is not None and (answer_label.text()).replace(" ", "") == "":
                                    writer.writerow([frame_name_label.text(), frameID_label.text()])

                self.last_csv_file = csv_file  # Update the most recent CSV file path
                QMessageBox.information(self, "Information", f"'{csv_file.split('/')[-1]}' was saved successfully.")
                print(f"CSV file '{csv_file}' saved successfully.")
            except Exception as e:
                print(f"Failed to save CSV file: {e}")


    def check_csv_file(self):
        if self.last_csv_file and os.path.exists(self.last_csv_file):
            try:
                if platform.system() == 'Windows':
                    os.startfile(self.last_csv_file)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.call(('open', self.last_csv_file))
                else:  # Linux and others
                    subprocess.call(('xdg-open', self.last_csv_file))
            except Exception as e:
                QMessageBox.critical(self, "Error Opening CSV", f"Failed to open CSV file: {e}")
        else:
            QMessageBox.warning(self, "No CSV File", "No CSV file found.")


    def compress_csv_folder(self):
        # Yêu cầu người dùng chọn thư mục chứa các tệp CSV
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")

        if folder:
            # Tên tệp zip đầu ra dựa trên tên thư mục đã chọn
            folder_name = os.path.basename(folder)
            zip_filename = os.path.join(os.path.dirname(folder), f"{folder_name}.zip")

            try:
                # Tạo tệp zip và thêm tất cả các tệp trong thư mục đã chọn vào đó
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            if file.endswith('.csv'):
                                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), folder))

                QMessageBox.information(self, "Success", f"'{zip_filename.split('/')[-1]}' have been compressed 'csv_data/'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to compress folder: {e}")
            


class TranslationApp(QObject):  # Kế thừa từ QObject để sử dụng pyqtSignal
    # Tín hiệu phát ra để yêu cầu mở cửa sổ kết quả
    show_result_signal = pyqtSignal(str, list, list, list)

    def __init__(self):
        super().__init__()
        self.app = QApplication([])
        self.main_win = QWidget()

        self.main_win.resize(500, 200)
        self.main_win.setWindowTitle("Retrieval App")

        self.input_label = QLabel("<b>Enter text to translate:</b>")
        self.input_text = QTextEdit()  # Changed to QTextEdit for better text handling
        self.translate_button = QPushButton("Translate")

        self.translator = Translator()

        self.set_layout()
        self.process_button()

        # Kết nối tín hiệu với phương thức để mở cửa sổ kết quả
        self.show_result_signal.connect(self.show_result_window)

    def set_layout(self):
        line = QVBoxLayout()
        line.addWidget(self.input_label)
        line.addWidget(self.input_text)
        line.addWidget(self.translate_button)
        self.main_win.setLayout(line)

    def translate_text(self):
        input_text = self.input_text.toPlainText()  # Get text from QTextEdit
        if input_text:
            try:
                response = self.translator.translate(input_text, dest='en')  # Use Google Translate API
                translated_text = response.text
                sio.emit('translated_text', {'text': translated_text})  # Gửi bản dịch tới server
                print(f"Translated text: {translated_text}")
                self.translated_text = translated_text  # Lưu lại bản dịch để sử dụng sau khi nhận được phản hồi
            except Exception as e:
                error_message = f"Translation failed: {e}"
                print(error_message)
        else:
            print("Please enter text to translate.")

    def extract_phrases(self, sentence):
        doc = nlp(sentence)

        # Extract numbers
        numbers = [token.text for token in doc if token.pos_ == 'NUM']
        
        # Extract letters
        letters = [token.text for token in doc if len(token.text) == 1 and token.text.isalpha()]

        # Extract special characters (punctuation)
        special_characters = [token.text for token in doc if token.pos_ == 'PUNCT']

        return numbers, letters, special_characters

    def show_result_window(self, translated_text, num, lett, char):
        self.result_window = ResultWindow(translated_text, num, lett, char)
        self.result_window.show()

    def process_button(self):
        self.translate_button.clicked.connect(self.translate_text)

    def run(self):
        self.main_win.show()
        self.app.exec_()


if __name__ == "__main__":
    app = TranslationApp()
    app.run()
