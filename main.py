import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from PIL import Image
import os
import tempfile

# 사용자로부터 ukg.db 파일 경로를 입력받는 부분
st.title("Windows System Recall - Window Capture Events")

db_file = st.file_uploader("Upload your ukg.db file", type="db")

if db_file is not None:
    # 업로드된 파일을 임시 디렉토리에 저장
    with tempfile.NamedTemporaryFile(delete=False) as temp_db:
        temp_db.write(db_file.read())
        temp_db_path = temp_db.name  # 임시 db 파일 경로

    # 업로드된 파일의 상위 폴더에 ImageStore 폴더가 있는지 확인
    base_dir = os.path.dirname(temp_db_path)
    image_base_dir = os.path.join(base_dir, "ImageStore")

    # ImageStore 폴더 확인
    if not os.path.exists(image_base_dir):
        st.error("ImageStore 폴더가 ukg.db 파일과 동일한 디렉토리에 존재하지 않습니다.")
    else:
        # DB 연결 설정
        conn = sqlite3.connect(temp_db_path)

        # WindowCapture 테이블에서 데이터 불러오기
        query_windowcapture = """
            SELECT WindowCapture.TimeStamp as Timestamp, 
                   WindowCapture.Name as EventName, 
                   WindowCapture.WindowTitle as WindowTitle, 
                   WindowCapture.WindowId as WindowId,
                   WindowCapture.IsForeground as IsForeground,
                   App.Path as Process, 
                   WindowCaptureTextIndex_content.c2 as OcrText,
                   ImageToken
            FROM WindowCaptureTextIndex_content 
            INNER JOIN WindowCapture ON WindowCapture.Id == WindowCaptureTextIndex_content.c0 
            INNER JOIN WindowCaptureAppRelation ON WindowCaptureAppRelation.WindowCaptureId == WindowCaptureTextIndex_content.c0 
            INNER JOIN App ON App.Id == WindowCaptureAppRelation.AppId 
            WHERE WindowCapture.Name == "WindowCaptureEvent" AND OcrText IS NOT NULL
        """

        # 각각의 데이터를 DataFrame으로 로드
        df_windowcapture = pd.read_sql_query(query_windowcapture, conn)

        # Timestamp 값을 변환하여 읽기 쉬운 형식으로 변경
        df_windowcapture['Timestamp'] = df_windowcapture['Timestamp'].apply(
            lambda x: (datetime.utcfromtimestamp(x / 1000) + timedelta(hours=9)).strftime('%Y.%m.%d(%a) %H:%M:%S GMT+0900'))

        # 첫 번째 창: Window Capture 데이터 표시
        st.subheader("Window Capture Events")
        st.dataframe(df_windowcapture)

        # 이미지 목록을 위한 선택 옵션 만들기
        image_tokens = df_windowcapture['ImageToken'].tolist()
        selected_image_token = st.selectbox("Select an image to view", image_tokens)

        # 선택된 이미지를 크게 보여줌
        selected_image_path = os.path.join(image_base_dir, f"{selected_image_token}.jpeg")

        if os.path.exists(selected_image_path):
            selected_image = Image.open(selected_image_path)
            st.image(selected_image, caption=f"Selected Image - {selected_image_token}", use_column_width=True)
        else:
            st.write(f"Selected image not found for ImageToken: {selected_image_token}")

        # 이미지들을 옆으로 나열하여 표시
        st.subheader("Captured Images")
        num_columns = 5  # 한 줄에 표시할 이미지의 수
        columns = st.columns(num_columns)

        for index, row in df_windowcapture.iterrows():
            image_path = os.path.join(image_base_dir, f"{row['ImageToken']}.jpeg")

            # 이미지가 존재할 경우에만 표시
            if os.path.exists(image_path):
                # 가로로 나열하기 위해서 열에 이미지 추가
                with columns[index % num_columns]:
                    image = Image.open(image_path)
                    st.image(image, caption=f"{row['WindowTitle']}", use_column_width=True)
            else:
                st.write(f"Image not found for ImageToken: {row['ImageToken']}")

        # 데이터베이스 연결 종료
        conn.close()

else:
    st.info("ukg.db 파일을 업로드해 주세요.")
