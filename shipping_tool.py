import streamlit as st
import gspread
import pandas as pd
import re
import datetime
from datetime import datetime as dt
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# =========================
# 1. CẤU HÌNH TRANG
# =========================
st.set_page_config(layout="wide", page_title="Quản lý phí Ship")

# =========================
# 2. TIỆN ÍCH SIDEBAR (NGÀY & THỜI TIẾT) - ĐÃ FIX MÚI GIỜ VN
# =========================
now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
thu_tieng_viet = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
thu = thu_tieng_viet[now.weekday()]
ngay_hien_tai = f"{thu}, ngày {now.strftime('%d/%m/%Y')}"

gio = now.hour
if 6 <= gio < 17:
    thoi_tiet = "Trời đang nắng đẹp ☀️"
elif 17 <= gio < 19:
    thoi_tiet = "Hoàng hôn lãng mạn 🌇"
else:
    thoi_tiet = "Trời đêm mát mẻ ✨"

# =========================
# 3. STYLE CSS TỔNG HỢP (SỬA LỖI LỀ TRÊN & ẨN NÚT HTML KHI IN)
# =========================
st.markdown("""
<style>
    .block-container { padding: 2rem 3rem; max-width: 100%; }
    
    /* Đổi màu tiêu đề st.title */
    h1 { color: #5B7E3C !important; }

    /* Taskbar sidebar */
    .taskbar-box {
        background-color: #f1f4ef; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #5B7E3C; margin-bottom: 20px;
    }
    
    /* Header bảng */
    div[data-testid="stHorizontalBlock"]:has(.header-col) { gap: 0px !important; }
    .header-col {
        background-color: #5B7E3C; color: white; font-weight: bold;
        font-size: 18px; padding: 12px 5px; text-align: center;
        border-right: 0.1px solid #ffffff33;
    }
    .header-left { border-radius: 8px 0 0 0; }
    .header-right { border-radius: 0 8px 0 0; border-right: none; }
    
    /* Nội dung dòng bảng */
    .row-style {
        font-size: 18px; padding: 10px 0; display: flex;
        align-items: center; justify-content: center;
    }
    
    /* Tổng cộng tháng */
    .total-box {
        padding: 18px; border-radius: 15px; font-size: 22px;
        font-weight: bold; text-align: center;
        background-color: #5B7E3C; color: white;
        box-shadow: 0 4px 15px rgba(91, 126, 60, 0.3);
        margin-top: 20px;
    }

    /* Đổi màu các nút bấm Streamlit mặc định */
    .stButton > button {
        border-color: #5B7E3C !important;
        color: #5B7E3C !important;
    }
    .stButton > button:hover {
        background-color: #5B7E3C !important;
        color: white !important;
    }

    /* Tiêu đề ẩn trên web, chỉ hiện khi in */
    .print-title { display: none; }

    /* =========================================
       CSS ĐỊNH DẠNG RIÊNG KHI BẤM IN (PRINT)
       ========================================= */
    @media print {
        @page {
            size: landscape;
            margin: 5mm 10mm 10mm 10mm; /* Ép sát lề trên 5mm */
        }
        
        /* Ẩn toàn bộ các phần giao diện phụ bao gồm cả nút In bằng HTML */
        section[data-testid="stSidebar"], 
        div[data-testid="stForm"], 
        div.stSelectbox,
        header, 
        footer,
        h1,
        iframe,
        [data-testid="stHeader"],
        div.stButton,
        .no-print { 
            display: none !important; 
        }
        
        /* TRIỆT TIÊU TOÀN BỘ KHOẢNG TRẮNG ĐỆM PHÍA TRÊN CỦA STREAMLIT */
        .main, .main .block-container, [data-testid="stMainBlockContainer"] {
            padding-top: 0px !important;
            margin-top: 0px !important;
            top: 0px !important;
        }

        /* Hiện tiêu đề in chuyên nghiệp */
        .print-title {
            display: block !important;
            color: #5B7E3C !important;
            text-align: center !important;
            margin-top: 0px !important;
            margin-bottom: 25px !important;
            font-size: 24px !important;
            font-weight: bold !important;
        }

        /* Định dạng lại bảng dòng để không bị lệch form */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            width: 100% !important;
            gap: 0px !important;
        }

        /* Ẩn cột Xóa (cột số 6) */
        div[data-testid="stHorizontalBlock"] > div:nth-child(6) {
            display: none !important;
        }

        /* Ép layout dòng chia tỉ lệ chuẩn khổ giấy ngang */
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) { width: 6% !important; max-width: 6% !important; flex: 0 0 6% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) { width: 14% !important; max-width: 14% !important; flex: 0 0 14% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(3) { width: 50% !important; max-width: 50% !important; flex: 0 0 50% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(4) { width: 15% !important; max-width: 15% !important; flex: 0 0 15% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(5) { 
            width: 15% !important; max-width: 15% !important; flex: 0 0 15% !important;
            border-right: none !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.header-col) > div:nth-child(5) .header-col {
            border-radius: 0 8px 0 0 !important;
        }

        .row-style, .header-col { font-size: 15px !important; padding: 6px 2px !important; }
    }
</style>
""", unsafe_allow_html=True)

# =========================
# 4. KẾT NỐI GOOGLE SHEETS
# =========================
SHEET_ID = "1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg"

@st.cache_resource
def ket_noi_sheet():
    s = st.secrets
    creds_dict = {
        "type": s["type"], "project_id": s["project_id"], "private_key_id": s["private_key_id"],
        "private_key": s["private_key"], "client_email": s["client_email"], "client_id": s["client_id"],
        "auth_uri": s["auth_uri"], "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).sheet1

ws = ket_noi_sheet()

# =========================
# 5. SIDEBAR GIAO DIỆN
# =========================
with st.sidebar:
    st.markdown(f'''
    <div class="taskbar-box">
        <p style="margin:0; font-size: 14px; color: #555;">📅 <b>Hôm nay:</b></p>
        <p style="margin:0; font-size: 16px; font-weight: bold;">{ngay_hien_tai}</