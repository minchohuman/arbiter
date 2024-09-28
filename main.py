import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# DB 연결 설정
conn = sqlite3.connect('ukg.db')  # 데이터베이스 파일 경로를 지정하세요.

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

# Web 테이블에서 URI 데이터 가져오기 (SQL 쿼리)
query_web = """
    SELECT Web.Uri as Uri
    FROM Web
"""

# 각각의 데이터를 DataFrame으로 로드
df_windowcapture = pd.read_sql_query(query_windowcapture, conn)
df_web = pd.read_sql_query(query_web, conn)

# Timestamp 값을 변환하여 읽기 쉬운 형식으로 변경
df_windowcapture['Timestamp'] = df_windowcapture['Timestamp'].apply(lambda x: (datetime.utcfromtimestamp(x / 1000) + timedelta(hours=9)).strftime('%Y.%m.%d(%a) %H:%M:%S GMT+0900'))

# Streamlit 애플리케이션 설정
st.title('Windows System Recall - Window Capture and Web Events')

# 첫 번째 창: Window Capture 데이터 표시
st.subheader("Window Capture Events")
st.dataframe(df_windowcapture)

# 두 번째 창: Web 테이블 데이터 표시
st.subheader("Web Table Data (URI)")
st.dataframe(df_web)

# 데이터베이스 연결 종료
conn.close()
