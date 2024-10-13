#image_loader.py

from PySide6.QtWidgets import QDialog, QLabel, QScrollArea
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QThread, Signal, Qt

# 이미지 로드를 위한 스레드 클래스 정의
class ImageLoaderThread(QThread):
    image_loaded = Signal(QPixmap)  # 이미지 로드가 완료되면 QPixmap 객체를 신호로 전송

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path  # 로드할 이미지 경로 저장

    def run(self):
        print(f"이미지 경로 시도 중: {self.image_path}")  # 디버깅용 출력
        pixmap = QPixmap(self.image_path)
        if pixmap.isNull():
            print(f"이미지 로드 실패: {self.image_path}")  # 디버깅용 출력
            self.image_loaded.emit(QPixmap())
            return  # 이미지 경로를 통해 QPixmap 객체 생성
        # 이미지가 1280x960보다 크면 크기를 조정 (KeepAspectRatio로 비율 유지)
        if pixmap.width() > 1280 or pixmap.height() > 960:
            pixmap = pixmap.scaled(1280, 960, Qt.KeepAspectRatio)
        # 이미지 로드가 완료되면 image_loaded 신호를 통해 QPixmap 객체 전달
        self.image_loaded.emit(pixmap)

# 이미지를 보여주는 별도의 창을 담당하는 클래스 정의
class ImageWindow(QDialog):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Image Viewer")  # 창의 제목 설정
        self.setFixedSize(1280, 960)  # 창 크기를 고정 (1280x960)

        # 스크롤 가능한 영역 설정 (이미지가 창보다 클 경우 스크롤 가능)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setGeometry(10, 10, 1260, 940)  # 스크롤 영역의 위치와 크기 설정
        self.scroll_area.setWidgetResizable(True)
