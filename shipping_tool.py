import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import io
import os

# Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

# --- HÀM KẾT NỐI GOOGLE SHEETS ---
def connect_gsheet():
    # Kiểm tra xem file credentials.json có tồn tại không
    if not os.path.exists("credentials.json"):
        return None
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        # Thay "Du_Lieu_Ship" bằng tên chính xác file Google Sheet của Như
        sheet = client.open("Du_Lieu_Ship").sheet1
        return sheet
    except:
        return None

# --- HÀM LOAD DỮ LIỆU ---
def load_data():
    sheet = connect_gsheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                # Ép kiểu ngày tháng để tránh lỗi .dt accessor
                df['Ngày'] = pd.to_datetime(df['Ngày'], format='%d/%m/%Y', errors='coerce')
                return df.dropna(subset=['Ngày'])
        except:
            pass
    return pd.DataFrame(columns=["Ngày", "Nội dung", "Đơn vị vận chuyển", "Phí"])

# --- GIAO DIỆN ---
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# PHẦN NHẬP LIỆU
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        date_input = st.date_input("Ngày giao", datetime.now())
    with col2:
        content = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier = st.selectbox("Đơn vị", ["Ahamove", "Grab", "Lalamove", "Viettel post"])
        price = st.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu thông tin"):
        sheet = connect_gsheet()
        if sheet:
            new_row = [date_input.strftime('%d/%m/%Y'), content, carrier, price]
            sheet.append_row(new_row)
            st.success("Đã đồng bộ lên Google Sheets! ✨")
            st.session_state.df = load_data()
            st.rerun()
        else:
            st.error("Chưa kết nối được Google Sheets. Như hãy kiểm tra file credentials.json nhé!")

# Hiển thị danh sách và xuất Excel (Phần này Như giữ nguyên logic cũ mình đã gửi)