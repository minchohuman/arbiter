#main.py

import sys
import os
import math
from PySide6.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QFileDialog, QLabel, \
    QSplitter, QStatusBar, QStyledItemDelegate
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSortFilterProxyModel
from database import SQLiteTableModel, load_data_from_db
from image_loader import ImageLoaderThread
import sqlite3


# 특정 열의 텍스트를 가운데 정렬하는 delegate 클래스
class CenteredDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter  # 가운데 정렬 설정


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReCall DATA Parser")  # 프로그램 제목 설정
        self.resize(1200, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        self.table_view = QTableView()
        self.splitter.addWidget(self.table_view)

        self.image_label = QLabel("이미지 표시 창")  # 라벨 텍스트 변경
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(400, 600)
        self.splitter.addWidget(self.image_label)

        # 상태바 설정
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("파일")
        open_file_action = QAction("파일 열기", self)
        open_file_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_file_action)

        self.proxy_model = QSortFilterProxyModel(self)  # QSortFilterProxyModel 설정
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)

        self.db_path = ""

        self.table_view.selectionModel().selectionChanged.connect(self.update_image_display)

    def load_data(self, db_path):
        self.db_path = db_path
        data, headers = load_data_from_db(db_path)

        if data:
            # 새 열 추가: '이미지' 열 추가
            updated_data = []
            for row in data:
                row = list(row)  # 튜플을 리스트로 변환
                image_token = row[2]  # 3번째 열이 ImageToken 값이라고 가정
                if image_token:  # ImageToken 값이 있으면 'O'
                    row.append("O")
                else:  # ImageToken 값이 없으면 'X'
                    row.append("X")
                updated_data.append(row)  # 변환된 리스트를 새로운 데이터에 추가

            # 헤더에 새 열 이름 추가
            headers.append("이미지")

            model = SQLiteTableModel(updated_data, headers)
            self.proxy_model.setSourceModel(model)

            # 숨기려는 열의 인덱스를 지정하여 숨김 (ImageToken 열이 3번째 열이라고 가정)
            self.table_view.hideColumn(2)  # ImageToken 열 숨기기

            # ID, Name, TimeStamp 열만 자동으로 크기 조정
            self.table_view.resizeColumnToContents(0)  # ID 열 크기 자동 조정
            self.table_view.resizeColumnToContents(1)  # Name 열 크기 자동 조정
            self.table_view.resizeColumnToContents(5)  # TimeStamp 열 크기 자동 조정

            # "이미지" 열의 이름 길이에 맞춰 열의 너비 자동 조정
            self.table_view.resizeColumnToContents(len(headers) - 1)  # 마지막 열의 크기 조정

            # 이미지 열을 가운데 정렬로 설정
            centered_delegate = CenteredDelegate(self.table_view)
            self.table_view.setItemDelegateForColumn(len(headers) - 1, centered_delegate)

            # 삭제 여부 및 Next ID 확인 로직 실행
            self.check_deletion_and_calculate_next_id()
        else:
            self.status_bar.showMessage("데이터를 불러오지 못했습니다.")

    def check_deletion_and_calculate_next_id(self):
        """ 첫 번째 ID 값과 Next ID 값을 비교하고 삭제 여부를 O 또는 X로 표시 """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # WindowCapture 테이블에서 가장 작은 (첫 번째) ID 값을 찾음
            cursor.execute("SELECT MIN(Id) FROM WindowCapture;")
            first_id_row = cursor.fetchone()
            first_id = first_id_row[0] if first_id_row and first_id_row[0] is not None else 0

            # IdTable에서 Next ID 값을 확인
            cursor.execute("SELECT * FROM IdTable;")
            next_id_row = cursor.fetchone()
            next_id = next_id_row[0] if next_id_row else 0

            # 삭제 여부 확인 (비교 논리를 구현)
            if first_id == 0 or next_id != first_id + 1:
                deletion_status = "O"  # 삭제된 항목이 있음
            else:
                deletion_status = "X"  # 삭제된 항목이 없음

            # 상태바에 삭제 여부 표시
            self.status_bar.showMessage(f"삭제 여부: {deletion_status}, 첫 ID: {first_id}, Next ID: {next_id}")

            conn.close()

        except Exception as e:
            self.status_bar.showMessage(f"삭제 여부 확인 실패: {str(e)}")

    def open_file_dialog(self):
        db_path, _ = QFileDialog.getOpenFileName(self, "데이터베이스 파일 선택", "", "SQLite Files (*.db)")
        if db_path:
            self.load_data(db_path)

    def update_image_display(self, selected, deselected):
        """ 이미지 토큰 열이 있는 행의 아무 열을 클릭하면 이미지를 표시 """
        for index in selected.indexes():
            row = index.row()  # 선택된 행의 인덱스를 가져옴
            image_token_index = self.proxy_model.index(row, 2)  # 3번째 열이 ImageToken 값인 열이라고 가정
            image_token = image_token_index.data()  # ImageToken 값을 가져옴

            if image_token:  # ImageToken 값이 존재하는지 확인
                # 이미지 디렉토리 경로 설정
                image_dir = os.path.join(os.path.dirname(self.db_path), "ImageStore")
                image_path = os.path.join(image_dir, image_token)

                # 경로 확인을 위해 추가한 디버그 메시지
                print(f"이미지 파일 경로: {image_path}")

                # 파일이 존재하지 않는 경우
                if not os.path.exists(image_path):
                    self.image_label.setText(f"이미지 파일을 찾을 수 없습니다: {image_token}")
                    print(f"이미지 파일을 찾을 수 없습니다: {image_path}")  # 디버깅 메시지 추가
                    return

                # 스레드에서 이미지 로드
                self.load_image_in_thread(image_path)
                break  # 첫 번째 선택 항목에 대해 이미지를 표시한 후, 반복 종료

    def load_image_in_thread(self, image_path):
        # 이미지 로더 스레드를 사용하여 이미지 로드
        self.image_loader_thread = ImageLoaderThread(image_path)
        self.image_loader_thread.image_loaded.connect(self.display_image)

        self.image_loader_thread.start()

    def display_image(self, pixmap):
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
