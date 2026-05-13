import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

DATA_FILE = "shipping_data.csv"

# --- HÀM LOAD DỮ LIỆU ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            df['Ngày'] = pd.to_datetime(df['Ngày'], format='%d.%m.%Y', errors='coerce')
            return df.dropna(subset=['Ngày'])
        except:
            return pd.DataFrame(columns=["Ngày", "Nội dung", "ĐVVC", "Phí"])
    return pd.DataFrame(columns=["Ngày", "Nội dung", "ĐVVC", "Phí"])

# TỰ ĐỘNG LÀM MỚI (Dùng fragment để web tự chạy lại sau mỗi 60 giây)
@st.fragment(run_every=60)
def auto_refresh_data():
    st.session_state.df = load_data()

auto_refresh_data()

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# Nút cập nhật nhanh
if st.button("🔄 Cập nhật dữ liệu mới"):
    st.session_state.df = load_data()
    st.rerun()

# --- PHẦN NHẬP LIỆU ---
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns([1.5, 3, 2, 1.5])
    with col1:
        date = st.date_input("Ngày giao", datetime.now())
    with col2:
        content = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier = st.selectbox("Đơn vị", ["Lalamove 🚛", "Ahamove 🛵", "Grab 🚗", "Viettel Post 📦"])
    with col4:
        price = st.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu chuyến mới"):
        if content and price > 0:
            new_row = pd.DataFrame({
                "Ngày": [pd.to_datetime(date)],
                "Nội dung": [content],
                "ĐVVC": [carrier],
                "Phí": [price]
            })
            # Đọc lại dữ liệu mới nhất trước khi lưu để tránh đè dữ liệu của nhân viên khác
            current_df = load_data()
            updated_df = pd.concat([current_df, new_row], ignore_index=True)
            updated_df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            st.session_state.df = updated_df
            st.success("Đã lưu thành công! ✨")
            st.rerun()

# --- HIỂN THỊ DỮ LIỆU & XUẤT EXCEL ---
if not st.session_state.df.empty:
    st.write("---")
    df_show = st.session_state.df.copy()
    df_show['Ngày'] = df_show['Ngày'].dt.strftime('%d.%m.%Y')
    st.dataframe(df_show, use_container_width=True)

    # --- XỬ LÝ XUẤT EXCEL (GIỮ ĐỊNH DẠNG XỊN) ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df = st.session_state.df.copy()
        export_df['Ngày'] = export_df['Ngày'].dt.strftime('%d.%m.%Y')
        export_df.to_excel(writer, index=False, sheet_name='Báo cáo', startrow=0)
        
        workbook  = writer.book
        worksheet = writer.sheets['Báo cáo']
        
        # Định dạng
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center'})
        border_fmt = workbook.add_format({'border': 1})
        money_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0 "đ"'})
        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'num_format': '#,##0 "đ"'})
        total_label_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'align': 'center'})

        # Kẻ sẵn 30 dòng trống
        for r in range(1, 31):
            for c in range(4):
                worksheet.write(r, c, "", border_fmt)
        
        # Ghi đè dữ liệu thực tế
        for i, row in enumerate(export_df.values):
            worksheet.write(i+1, 0, row[0], border_fmt)
            worksheet.write(i+1, 1, row[1], border_fmt)
            worksheet.write(i+1, 2, row[2], border_fmt)
            worksheet.write(i+1, 3, row[3], money_fmt)

        # Dòng Tổng cộng ở dòng 32 (index 31)
        total_val = st.session_state.df['Phí'].sum()
        worksheet.merge_range(31, 0, 31, 2, "TỔNG CỘNG", total_label_fmt)
        worksheet.write(31, 3, total_val, total_fmt)

        # Căn chỉnh độ rộng cột
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 18)

    st.download_button(
        label="📥 Tải file Excel Báo cáo",
        data=output.getvalue(),
        file_name=f"Bao_cao_phi_ship_{datetime.now().strftime('%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Chưa có dữ liệu Như ơi! ✨")