#image_table.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDateTimeEdit, QGridLayout
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QPixmap  # 이미지 로딩을 위한 QPixmap 추가
import sqlite3
from datetime import datetime  # 날짜 변환을 위한 모듈 추가

class ImageTableWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = None  # 초기에는 db_path가 설정되지 않음
        self.images = []  # 이미지 리스트 저장
        self.current_image_index = 0  # 현재 보고 있는 이미지의 인덱스
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # 전체 여백을 최소화
        
        # 타임스탬프 범위 선택 위젯
        timestamp_layout = QHBoxLayout()
        timestamp_layout.setContentsMargins(0, 0, 0, 0)  # 여백 최소화
        self.start_time = QDateTimeEdit(QDateTime.currentDateTime())
        self.end_time = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        
        search_button = QPushButton("검색")
        search_button.clicked.connect(self.search_images_by_timestamp)
        
        timestamp_layout.addWidget(QLabel("시작 시간:"))
        timestamp_layout.addWidget(self.start_time)
        timestamp_layout.addWidget(QLabel("종료 시간:"))
        timestamp_layout.addWidget(self.end_time)
        timestamp_layout.addWidget(search_button)
        
        layout.addLayout(timestamp_layout)

        # 이미지 및 텍스트의 수평 정렬 레이아웃
        image_and_label_layout = QHBoxLayout()
        image_and_label_layout.setAlignment(Qt.AlignCenter)  # 수평 중앙 정렬 설정
        image_and_label_layout.setContentsMargins(0, 0, 0, 0)  # 여백 최소화

        # 이전 이미지
        prev_image_layout = QVBoxLayout()
        self.prev_image = QLabel()
        self.prev_image.setAlignment(Qt.AlignCenter)
        self.prev_image.setFixedSize(300, 300)  # 이전 이미지 크기 확장
        prev_image_layout.addWidget(self.prev_image)
        prev_image_layout.setAlignment(Qt.AlignVCenter)  # 이전 이미지를 중앙에 맞추기
        image_and_label_layout.addLayout(prev_image_layout)

        # 현재 이미지
        current_image_layout = QVBoxLayout()
        self.image_display = QLabel()
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setFixedSize(500, 500)  # 현재 이미지 크기 확장
        current_image_layout.addWidget(self.image_display)
        current_image_layout.setAlignment(Qt.AlignVCenter)  # 현재 이미지를 중앙에 맞추기
        image_and_label_layout.addLayout(current_image_layout)

        # 다음 이미지
        next_image_layout = QVBoxLayout()
        self.next_image = QLabel()
        self.next_image.setAlignment(Qt.AlignCenter)
        self.next_image.setFixedSize(300, 300)  # 다음 이미지 크기 확장
        next_image_layout.addWidget(self.next_image)
        next_image_layout.setAlignment(Qt.AlignVCenter)  # 다음 이미지를 중앙에 맞추기
        image_and_label_layout.addLayout(next_image_layout)

        # 이미지 및 텍스트 레이아웃 추가
        layout.addLayout(image_and_label_layout)

        # 이전 이미지, 다음 이미지로 이동하는 버튼을 메타데이터 위로 배치
        navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("이전 이미지로 이동")
        self.prev_button.clicked.connect(self.show_previous_image)
        self.next_button = QPushButton("다음 이미지로 이동")
        self.next_button.clicked.connect(self.show_next_image)
        navigation_layout.addWidget(self.prev_button)
        navigation_layout.addWidget(self.next_button)
        layout.addLayout(navigation_layout)

        # 이미지 메타데이터
        metadata_layout = QGridLayout()
        self.timestamp_label = QLabel("TimeStamp: ")
        self.window_title_label = QLabel("WindowTitle: ")
        self.image_token_label = QLabel("ImageToken: ")
        self.ocr_text_label = QLabel("OCRText: ")
        metadata_layout.addWidget(self.timestamp_label, 0, 0)
        metadata_layout.addWidget(self.window_title_label, 0, 1)
        metadata_layout.addWidget(self.image_token_label, 1, 0)
        metadata_layout.addWidget(self.ocr_text_label, 1, 1)
        
        layout.addLayout(metadata_layout)
        
    def set_db_path(self, db_path):
        """db_path 설정 및 이미지 로드"""
        self.db_path = db_path
        self.load_images()
        self.set_default_time_range()  # 기본 시간 범위 설정

    def load_images(self):
        """ImageToken이 NULL이 아닌 가장 빠른 TimeStamp 이미지 로드"""
        if self.db_path is None:
            return  # db_path가 설정되지 않은 경우 로드를 중단
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = """
        SELECT wc.Timestamp, wc.WindowTitle, wc.ImageToken, text.c2 AS OCRText
        FROM WindowCapture wc
        LEFT JOIN WindowCaptureTextIndex_content text ON wc.Id = text.rowid
        WHERE wc.ImageToken IS NOT NULL
        ORDER BY wc.Timestamp ASC;
        """
        cursor.execute(query)
        self.images = cursor.fetchall()
        conn.close()

        if self.images:
            self.current_image_index = 0
            self.display_image(self.images[0])  # 가장 빠른 이미지 표시
            self.display_adjacent_images()  # 이전 및 다음 이미지 표시

    def search_images_by_timestamp(self):
        if self.db_path is None:
            return  # db_path가 설정되지 않은 경우 로드를 중단

        # 타임스탬프 범위를 초 단위로 변환
        start_timestamp = self.start_time.dateTime().toSecsSinceEpoch()  # 초 단위로 변환
        end_timestamp = self.end_time.dateTime().toSecsSinceEpoch()  # 초 단위로 변환
        
        print(f"검색 범위 (초): {start_timestamp} ~ {end_timestamp}")  # 타임스탬프 범위 출력

        # 타임스탬프 범위 내 이미지 검색
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = """
        SELECT wc.Timestamp, wc.WindowTitle, wc.ImageToken, text.c2 AS OCRText
        FROM WindowCapture wc
        LEFT JOIN WindowCaptureTextIndex_content text ON wc.Id = text.rowid
        WHERE wc.Timestamp BETWEEN ? AND ? AND wc.ImageToken IS NOT NULL
        ORDER BY wc.Timestamp;
        """
        cursor.execute(query, (start_timestamp, end_timestamp))
        self.images = cursor.fetchall()  # 검색된 이미지 리스트로 업데이트
        conn.close()

        if self.images:
            print(f"검색된 이미지 수: {len(self.images)}")  # 검색된 이미지 수 출력
            self.current_image_index = 0  # 검색 후 첫 번째 이미지로 인덱스 초기화
            self.display_image(self.images[0])  # 첫 번째 이미지를 표시
            self.display_adjacent_images()  # 이전 및 다음 이미지 표시
        else:
            # 검색 결과가 없는 경우 처리
            self.image_display.clear()
            self.image_display.setText("해당 범위 내 이미지가 없습니다.")
            self.prev_image.clear()
            self.prev_image.setText("")
            self.next_image.clear()
            self.next_image.setText("")


    def display_image(self, image_data):
        timestamp, window_title, image_token, ocr_text = image_data
        
        # Unix 타임스탬프를 사람이 읽을 수 있는 형식으로 변환
        readable_timestamp = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        
        # 현재 이미지의 메타데이터를 갱신
        self.timestamp_label.setText(f"TimeStamp: {readable_timestamp}")
        self.window_title_label.setText(f"WindowTitle: {window_title}")
        self.image_token_label.setText(f"ImageToken: {image_token}")
        self.ocr_text_label.setText(f"OCRText: {ocr_text}")
        
        # 이미지 로딩 (ImageStore에서 불러오기)
        image_path = f"ImageStore/{image_token}"
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_display.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio))  # 현재 이미지는 더 크게 표시
        else:
            self.image_display.setText("이미지를 로드할 수 없습니다.")  # 이미지가 없을 경우 메시지 표시

    def display_adjacent_images(self):
        """이전 이미지 및 다음 이미지 표시"""
        prev_index = self.current_image_index - 1
        next_index = self.current_image_index + 1

        # 이전 이미지 로딩
        if prev_index >= 0:
            prev_image_data = self.images[prev_index]
            prev_image_token = prev_image_data[2]  # ImageToken
            prev_image_path = f"ImageStore/{prev_image_token}"
            prev_pixmap = QPixmap(prev_image_path)
            if not prev_pixmap.isNull():
                self.prev_image.setPixmap(prev_pixmap.scaled(300, 300, Qt.KeepAspectRatio))  # 이전 이미지 크기 확장
            else:
                self.prev_image.setText("이전 이미지를 로드할 수 없습니다.")
        else:
            self.prev_image.clear()  # 이전 이미지가 없는 경우 이미지 초기화
            self.prev_image.setText("첫번째 이미지 입니다.")  # 첫 번째 이미지일 때 텍스트 출력

        # 다음 이미지 로딩
        if next_index < len(self.images):
            next_image_data = self.images[next_index]
            next_image_token = next_image_data[2]  # ImageToken
            next_image_path = f"ImageStore/{next_image_token}"
            next_pixmap = QPixmap(next_image_path)
            if not next_pixmap.isNull():
                self.next_image.setPixmap(next_pixmap.scaled(300, 300, Qt.KeepAspectRatio))  # 다음 이미지 크기 확장
            else:
                self.next_image.setText("다음 이미지를 로드할 수 없습니다.")
        else:
            self.next_image.clear()  # 다음 이미지가 없는 경우 이미지 초기화
            self.next_image.setText("마지막 이미지입니다.")  # 마지막 이미지일 때 텍스트 출력


    def show_previous_image(self):
        """이전 이미지로 이동"""
        if self.current_image_index > 0:  # 인덱스가 0보다 클 때만 이전 이미지로 이동
            self.current_image_index -= 1
            self.display_image(self.images[self.current_image_index])
            self.display_adjacent_images()


    def show_next_image(self):
        """다음 이미지로 이동"""
        if self.current_image_index < len(self.images) - 1:  # 인덱스가 이미지 리스트의 길이를 넘지 않도록 체크
            self.current_image_index += 1
            self.display_image(self.images[self.current_image_index])
            self.display_adjacent_images()


    def set_default_time_range(self):
        """ImageToken이 NULL이 아닌 TimeStamp 중 가장 처음과 가장 끝 값을 기본값으로 설정"""
        if self.db_path is None:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 가장 빠른 Timestamp와 가장 늦은 Timestamp 검색
        query = """
        SELECT MIN(wc.Timestamp), MAX(wc.Timestamp)
        FROM WindowCapture wc
        WHERE wc.ImageToken IS NOT NULL;
        """
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()

        if result:
            min_timestamp, max_timestamp = result
            min_time = QDateTime.fromSecsSinceEpoch(min_timestamp // 1000)
            max_time = QDateTime.fromSecsSinceEpoch(max_timestamp // 1000)
            self.start_time.setDateTime(min_time)
            self.end_time.setDateTime(max_time)
