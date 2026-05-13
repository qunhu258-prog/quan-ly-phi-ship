import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import gspread

# 1. Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

# --- KẾT NỐI GOOGLE SHEETS (Thay cho file CSV) ---
# Như lấy file JSON chìa khóa dán vào Secrets như mình hướng dẫn trước đó nhé
def connect_gsheet():
    try:
        credentials = st.secrets["connections"]["gsheets"]
        gc = gspread.service_account_from_dict(credentials)
        # Thay link file Sheets của Như vào đây
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/ID_CUA_NHU/edit")
        return sh.get_worksheet(0)
    except Exception as e:
        st.error(f"Lỗi kết nối Sheets: {e}")
        return None

sheet = connect_gsheet()

# 2. Các hàm bổ trợ dữ liệu (Sửa để đọc/ghi lên Sheets)
def load_data():
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df['Ngày'] = pd.to_datetime(df['Ngày'], dayfirst=True, errors='coerce')
            return df.dropna(subset=['Ngày'])
    return pd.DataFrame(columns=["Ngày", "Nội dung", "Đơn vị vận chuyển", "Phí"])

# Tạm thời giữ danh sách đơn vị vận chuyển trong bộ nhớ để tránh lỗi file
if 'carriers' not in st.session_state:
    st.session_state.carriers = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

# Khởi tạo dữ liệu vào bộ nhớ tạm
if 'df' not in st.session_state:
    st.session_state.df = load_data()

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# --- PHẦN 1: CÀI ĐẶT (Sidebar bên trái) ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    new_carrier = st.text_input("Thêm đơn vị mới")
    if st.button("Lưu đơn vị"):
        if new_carrier and new_carrier not in st.session_state.carriers:
            st.session_state.carriers.append(new_carrier)
            st.success(f"Đã thêm: {new_carrier}")
            st.rerun()
    
    st.write("---")
    carrier_to_del = st.selectbox("Chọn đơn vị muốn xóa", st.session_state.carriers)
    if st.button("🗑️ Xóa đơn vị vận chuyển"):
        st.session_state.carriers.remove(carrier_to_del)
        st.rerun()

# --- PHẦN 2: NÚT CẬP NHẬT (Đọc lại từ Sheets) ---
if st.button("🔄 Cập nhật dữ liệu (Hiển thị chuyến mới nhất)"):
    st.session_state.df = load_data()
    st.rerun()

# --- PHẦN 3: NHẬP LIỆU (Ghi thẳng lên Sheets) ---
st.subheader("➕ Thêm chuyến mới")
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        date = st.date_input("Ngày giao", datetime.now())
    with col2:
        content = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier = st.selectbox("Đơn vị vận chuyển", st.session_state.carriers)
        price = st.number_input("Phí vận chuyển (VNĐ)", min_value=0, step=1000, format="%d")
    
    submit = st.form_submit_button("💾 Lưu thông tin")

    if submit:
        if content and price > 0:
            # Tạo dòng mới
            new_row_data = [date.strftime('%d/%m/%Y'), content, carrier, price]
            
            # 1. Ghi trực tiếp vào Google Sheets
            if sheet:
                sheet.append_row(new_row_data)
                # 2. Cập nhật vào bộ nhớ hiển thị ngay
                st.session_state.df = load_data()
                st.balloons()
                st.rerun()

# --- PHẦN 4: HIỂN THỊ DANH SÁCH (Giữ nguyên giao diện của Như) ---
st.write("---")
st.subheader("📋 Danh sách chi phí")

if not st.session_state.df.empty:
    df_display = st.session_state.df.copy()
    df_display['Tháng_Năm'] = df_display['Ngày'].dt.strftime('%m/%Y')
    
    months = sorted(df_display['Tháng_Năm'].unique(), reverse=True)
    sel_month = st.selectbox("📅 Lọc theo tháng:", months)
    month_data = df_display[df_display['Tháng_Năm'] == sel_month].copy()
    
    if not month_data.empty:
        # (Phần hiển thị bảng và nút Xóa, xuất Excel Như giữ nguyên như code cũ nhé)
        # Mình chỉ thay đổi logic ghi/đọc ở trên để nó không bao giờ mất dữ liệu
        st.dataframe(month_data.iloc[::-1], use_container_width=True)
        
        total = month_data["Phí"].sum()
        st.info(f"💰 **Tổng cộng tháng {sel_month}: {total:,.0f} VNĐ**")