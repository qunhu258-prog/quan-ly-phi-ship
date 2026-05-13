import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# 1. Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

DATA_FILE = "shipping_data.csv"
CARRIER_FILE = "carriers.csv"

# 2. Hàm đọc/ghi dữ liệu (Dùng cache để tăng tốc và tránh lỗi)
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            # Đọc file với encoding utf-8-sig để tránh lỗi font tiếng Việt
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            # Đảm bảo cột Ngày đúng định dạng
            df['Ngày'] = pd.to_datetime(df['Ngày'], format='%d.%m.%Y', errors='coerce')
            return df.dropna(subset=['Ngày'])
        except:
            return pd.DataFrame(columns=["Ngày", "Nội dung", "ĐVVC", "Phí"])
    return pd.DataFrame(columns=["Ngày", "Nội dung", "ĐVVC", "Phí"])

def load_carriers():
    default_carriers = ["Lalamove 🚛", "Ahamove 🛵", "Grab 🚗", "Viettel Post 📦"]
    if os.path.exists(CARRIER_FILE):
        try:
            c_df = pd.read_csv(CARRIER_FILE, encoding='utf-8-sig')
            return c_df['Tên'].tolist()
        except:
            return default_carriers
    return default_carriers

# Khởi tạo dữ liệu ban đầu
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# 3. Tự động làm mới mỗi 60 giây
@st.fragment(run_every=60)
def auto_refresh():
    new_df = load_data()
    if len(new_df) != len(st.session_state.df):
        st.session_state.df = new_df

auto_refresh()

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# 4. Sidebar quản lý đơn vị
with st.sidebar:
    st.header("⚙️ Cài đặt đơn vị")
    new_c = st.text_input("Thêm đơn vị mới")
    if st.button("➕ Lưu đơn vị"):
        if new_c:
            c_list = load_carriers()
            if new_c not in c_list:
                c_list.append(new_c)
                pd.DataFrame(c_list, columns=['Tên']).to_csv(CARRIER_FILE, index=False, encoding='utf-8-sig')
                st.success("Đã thêm!")
                st.rerun()

    st.write("---")
    curr_c_list = load_carriers()
    to_del = st.selectbox("Chọn đơn vị muốn xóa", curr_c_list)
    if st.button("🗑️ Xóa đơn vị"):
        curr_c_list.remove(to_del)
        pd.DataFrame(curr_c_list, columns=['Tên']).to_csv(CARRIER_FILE, index=False, encoding='utf-8-sig')
        st.success("Đã xóa!")
        st.rerun()

# 5. Form nhập liệu (Đã sửa lỗi không hiển thị dòng mới)
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns([1.5, 3, 2, 1.5])
    with col1:
        date_val = st.date_input("Ngày giao", datetime.now())
    with col2:
        content_val = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier_val = st.selectbox("Đơn vị vận chuyển", load_carriers())
    with col4:
        price_val = st.number_input("Phí vận chuyển (VNĐ)", min_value=0, step=1000)
    
    submit = st.form_submit_button("💾 Lưu thông tin")
    
    if submit:
        if content_val and price_val > 0:
            # Tạo dòng mới
            new_data = {
                "Ngày": date_val.strftime('%d.%m.%Y'),
                "Nội dung": content_val,
                "ĐVVC": carrier_val,
                "Phí": price_val
            }
            new_df_row = pd.DataFrame([new_data])
            
            # Đọc lại dữ liệu cũ từ file để tránh mất dữ liệu nhân viên khác
            current_full_df = load_data()
            current_full_df['Ngày'] = current_full_df['Ngày'].dt.strftime('%d.%m.%Y')
            
            # Cộng dồn và lưu
            final_df = pd.concat([current_full_df, new_df_row], ignore_index=True)
            final_df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            
            # Cập nhật session để hiển thị ngay
            st.session_state.df = load_data()
            st.success("Đã lưu thành công!")
            st.rerun()
        else:
            st.error("Vui lòng nhập đầy đủ Nội dung và Phí > 0")

# 6. Hiển thị và Xuất Excel
if not st.session_state.df.empty:
    st.write("---")
    st.subheader("📋 Danh sách đã nhập")
    
    # Định dạng hiển thị bảng
    display_df = st.session_state.df.copy()
    display_df['Ngày'] = display_df['Ngày'].dt.strftime('%d.%m.%Y')
    st.dataframe(display_df, use_container_width=True)
    
    # Nút tải Excel (Giữ đúng mẫu 32 dòng của Như)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df = display_df.copy()
        export_df.to_excel(writer, index=False, sheet_name='Báo cáo')
        workbook, worksheet = writer.book, writer.sheets['Báo cáo']
        
        # Style định dạng
        fmt_border = workbook.add_format({'border': 1})
        fmt_money = workbook.add_format({'border': 1, 'num_format': '#,##0 "đ"'})
        fmt_total = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'num_format': '#,##0 "đ"'})
        
        # Kẻ khung 30 dòng trống
        for r in range(1, 31):
            for c in range(4): worksheet.write(r, c, "", fmt_border)
        
        # Ghi dữ liệu
        for i, row in enumerate(export_df.values):
            worksheet.write(i+1, 0, row[0], fmt_border)
            worksheet.write(i+1, 1, row[1], fmt_border)
            worksheet.write(i+1, 2, row[2], fmt_border)
            worksheet.write(i+1, 3, row[3], fmt_money)
            
        # Dòng tổng cộng (Dòng 32 trong Excel)
        total = st.session_state.df['Phí'].sum()
        worksheet.merge_range(31, 0, 31, 2, "TỔNG CỘNG", fmt_total)
        worksheet.write(31, 3, total, fmt_total)
        
    st.download_button("📥 Tải báo cáo Excel", output.getvalue(), "bao_cao.xlsx")
else:
    st.info("Chưa có dữ liệu Như ơi! ✨")