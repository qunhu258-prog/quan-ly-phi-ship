import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# CONFIG SHEET ID
# =========================
SHEET_ID = "1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg"

# =========================
# CONNECT GOOGLE SHEETS (DEBUG VERSION)
# =========================
@st.cache_resource
def get_conn():

    try:
        st.write("🔵 Bước 1: Đọc secrets...")

        s = st.secrets

        creds_dict = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": s["private_key"],
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }

        st.success("✅ Đọc secrets OK")

        # =========================
        # AUTH GOOGLE
        # =========================
        st.write("🔵 Bước 2: Authenticate Google...")

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=scope
        )

        gc = gspread.authorize(creds)

        st.success("✅ Auth Google OK")

        # =========================
        # TEST LIST FILES
        # =========================
        st.write("🔵 Bước 3: Test quyền Drive...")

        try:
            files = gc.list_spreadsheet_files()
            st.write("📄 File Google Sheets nhìn thấy:")
            st.write(files)
        except Exception as e:
            st.error("❌ Không list được file (lỗi quyền Drive)")
            st.exception(e)

        # =========================
        # OPEN SHEET
        # =========================
        st.write("🔵 Bước 4: Mở Google Sheet...")

        try:
            sh = gc.open_by_key(SHEET_ID)
            st.success("✅ Mở Sheet thành công")
        except Exception as e:
            st.error("❌ Lỗi khi mở Google Sheet (QUAN TRỌNG)")
            st.exception(e)
            st.stop()

        # =========================
        # GET WORKSHEET
        # =========================
        ws = sh.sheet1
        st.success("✅ Kết nối worksheet OK")

        return ws

    except Exception as e:
        st.error("❌ Lỗi tổng khi kết nối Google")
        st.exception(e)
        return None


# =========================
# UI
# =========================
st.set_page_config(page_title="Debug Ship Tool", layout="wide")

st.title("🚚 DEBUG TOOL QUẢN LÝ PHÍ SHIP")

ws = get_conn()

if ws is None:
    st.stop()

# =========================
# TEST READ DATA
# =========================
st.write("🔵 Bước 5: Đọc dữ liệu...")

try:
    data = ws.get_all_values()
    st.write("📊 Raw data:", data)

except Exception as e:
    st.error("❌ Lỗi đọc dữ liệu sheet")
    st.exception(e)
    st.stop()

# =========================
# TEST WRITE DATA
# =========================
st.write("🔵 Bước 6: Test ghi dữ liệu...")

if st.button("Test ghi 1 dòng"):

    try:
        ws.append_row([
            datetime.now().strftime("%d/%m/%Y"),
            "TEST DEBUG",
            "Ahamove",
            10000
        ])

        st.success("✅ Ghi dữ liệu OK")

    except Exception as e:
        st.error("❌ Lỗi ghi dữ liệu")
        st.exception(e)