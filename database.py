#database.py

from PySide6.QtCore import QAbstractTableModel, Qt
from datetime import datetime, timedelta, timezone
import sqlite3

def convert_unix_timestamp(timestamp):
    return (datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc) + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')

class SQLiteTableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data  # 데이터를 테이블에 저장
        self.headers = headers  # 테이블 헤더

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data[index.row()][index.column()]

            # TimeStamp 열에 대한 특별 처리
            if self.headers[index.column()] == "TimeStamp":
                return convert_unix_timestamp(value)

            return value

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0]) if self._data else 0

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

def load_data_from_db(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 데이터베이스 쿼리
        query = """
        SELECT 
            wc.Id, wc.Name, wc.ImageToken, wc.WindowTitle, 
            app.Name AS AppName, wc.TimeStamp, file.Path AS FilePath, web.Uri AS WebUri
        FROM WindowCapture wc
        LEFT JOIN WindowCaptureAppRelation war ON wc.Id = war.WindowCaptureId
        LEFT JOIN App app ON war.AppId = app.Id
        LEFT JOIN WindowCaptureFileRelation wfr ON wc.Id = wfr.WindowCaptureId
        LEFT JOIN File file ON wfr.FileId = file.Id
        LEFT JOIN WindowCaptureWebRelation wwr ON wc.Id = wwr.WindowCaptureId
        LEFT JOIN Web web ON wwr.WebId = web.Id
        ORDER BY wc.Id;
        """
        cursor.execute(query)
        data = cursor.fetchall()
        headers = ["Id", "Name", "ImageToken", "WindowTitle", "AppName", "TimeStamp", "FilePath", "WebUri"]

        conn.close()
        return data, headers

    except Exception as e:
        print(f"DB 로드 오류: {str(e)}")
        return None, None
