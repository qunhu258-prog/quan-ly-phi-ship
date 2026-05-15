import streamlit as st
import gspread
import pandas as pd
import re
import datetime
from datetime import datetime as dt
from google.oauth2.service_account import Credentials

# =========================
# FULL WIDTH & CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Quản lý phí Ship")

# =========================
# TIỆN ÍCH: NGÀY & THỜI TIẾT (TASKBAR TRÊN SIDEBAR)
# =========================
now = datetime.datetime.now()
thu_tieng_viet = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
thu = thu_tieng_viet[now.weekday()]
ngay_hien_tai = f"{thu}, ngày {now.strftime('%d/%m/%Y')}"

# Giả lập thời tiết theo giờ thực tế
gio = now.hour
if 6 <= gio < 17:
    thoi_tiet = "Trời đang nắng đẹp ☀️"
elif 17 <= gio < 19:
    thoi_tiet = "Hoàng hôn lãng mạn 🌇"
else:
    thoi_tiet = "Trời đêm mát mẻ ✨"

# =========================
# STYLE TỔNG HỢP
# =========================
st.markdown("""
<style>
.block-container { padding: 2rem 3rem; max-width: 100%; }

/* Style cho Sidebar Taskbar */
.taskbar-box {
    background-color: #f0f2f6; 
    padding: 15px; 
    border-radius: 10px; 
    border-left: 5px solid #1f77b4; 
    margin-bottom: 20px;
}

/* HEADER BẢNG */
div[data-testid="stHorizontalBlock"]:has(.header-col) { gap: 0px !important; }
.header-col {
    background-color: #1f77b4;
    color: white;
    font-weight: bold;
    font-size: 18px;
    padding: 12px 5px;
    text-align: center;
    border-right: 0.1px solid #ffffff33;
}
.header-left { border-radius: 8px 0 0 0; }
.header-right { border-radius: 0 8px 0 0; border-right: none; }

/* DÒNG DỮ LIỆU */
.row-style {
    font-size: 18px; 
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 10px 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* CĂN GIỮA NÚT XOÁ */
[data-testid="column"]:last-child {
    display: flex;
    justify-content: center;
    align-items: center;
}

/* TOTAL BOX */
.total-box {
    padding: 18px;
    border-radius: 15px;
    font-size: 22px;
    font-weight: bold;
    text-align: center;
    background: linear-gradient(90deg,#ffeaa7,#fab1a0);
}
</style>
""", unsafe_allow_html=True)

# =========================
# CONNECT SHEET
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
# TITLE & SIDEBAR
# =========================
st.title("🚚 CHI PHÍ GIAO HÀNG")

with st.sidebar:
    # Hiển thị Taskbar Ngày & Thời tiết
    st.markdown(f"""
    <div class="taskbar-box">
        <p style="margin:0; font-size: 14px; color: #555;">📅 <b>Hôm nay:</b></p>
        <p style="margin:0; font-size: 16px; font-weight: bold;">{ngay_hien_tai}</p>
        <hr style="margin: 10px 0; border: 0.5px solid #ddd;">
        <p style="margin:0; font-size: 14px; color: #555;">🌤️ <b>Thời tiết:</b></p>
        <p style="margin:0; font-size: 16px;">{thoi_tiet}</p>
    </div>
    """, unsafe_allow_html=True)

    st.header("⚙️ Đơn vị vận chuyển")
    if "ds_donvi" not in st.session_state:
        st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

    new = st.text_input("Thêm đơn vị")
    if st.button("➕ Thêm"):
        if new and new not in st.session_state