import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# 1. Cấu hình
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

DATA_FILE = "shipping_data.csv"

# 2. Hàm đọc dữ liệu (Chỉ đọc lần đầu tiên khi mở App)
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            df['Ngày'] = pd.to_datetime(df['Ngày'], errors='coerce')
            return df.dropna(subset=['Ngày'])
        except:
            return pd.DataFrame(columns=["Ngày", "Nội dung", "Đơn vị vận chuyển", "Phí"])
    return pd.DataFrame(columns=["Ngày", "Nội dung", "Đơn vị vận chuyển", "Phí"])

# Khởi tạo bộ nhớ tạm (Session State) - Đây là nơi giữ dữ liệu cho nhân viên thấy
if 'df' not in st.session_state:
    st.session_state.df = load_data()

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# --- NÚT CẬP NHẬT (ĐÚNG Ý NHƯ YÊU CẦU) ---
# Nút này sẽ làm mới giao diện để hiện dữ liệu trong bộ nhớ mà không cần F5
if st.button("🔄 Cập nhật dữ liệu (Hiển thị chuyến mới nhất)"):
    # Chỉ cần rerun để giao diện vẽ lại các dòng trong st.session_state.df
    st.rerun() 

# --- FORM NHẬP LIỆU ---
st.subheader("➕ Thêm chuyến mới")
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        date = st.date_input("Ngày giao", datetime.now())
    with col2:
        content = st.text_input("Nội dung đơn hàng")
    with col3:
        # Giữ danh sách cố định hoặc Như có thể thêm sidebar như cũ
        carrier = st.selectbox("Đơn vị vận chuyển", ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"])
        price = st.number_input("Phí vận chuyển (VNĐ)", min_value=0, step=1000, format="%d")
    
    submit = st.form_submit_button("💾 Lưu thông tin")

    if submit:
        if content and price > 0:
            new_row = pd.DataFrame({
                "Ngày": [pd.to_datetime(date)],
                "Nội dung": [content],
                "Đơn vị vận chuyển": [carrier],
                "Phí": [price]
            })
            # Cập nhật vào bộ nhớ tạm ngay lập tức
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            
            # Ghi vào file để lưu trữ
            st.session_state.df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            
            st.success("Đã lưu thành công! Nhân viên có thể thấy bên dưới.")
            st.rerun()

# --- HIỂN THỊ DANH SÁCH ---
st.write("---")
if not st.session_state.df.empty:
    # Hiển thị bảng dữ liệu từ bộ nhớ tạm (Session State)
    # Nhân viên sẽ luôn thấy dữ liệu họ vừa nhập ở đây
    df_display = st.session_state.df.copy()
    df_display['Ngày'] = df_display['Ngày'].dt.strftime('%d.%m.%Y')
    
    # Đảo ngược bảng để chuyến mới nhất nằm lên đầu cho dễ xem
    st.dataframe(df_display.iloc[::-1], use_container_width=True) 
else:
    st.info("Chưa có dữ liệu Như ơi! ✨")