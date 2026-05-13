import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

DATA_FILE = "shipping_data.csv"
CARRIER_FILE = "carriers.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            df['Ngày'] = pd.to_datetime(df['Ngày'], errors='coerce')
            return df.dropna(subset=['Ngày'])
        except:
            return pd.DataFrame(columns=["Ngày", "Nội dung", "Đơn vị vận chuyển", "Phí"])
    return pd.DataFrame(columns=["Ngày", "Nội dung", "Đơn vị vận chuyển", "Phí"])

def load_carriers():
    if os.path.exists(CARRIER_FILE):
        try:
            return pd.read_csv(CARRIER_FILE, encoding='utf-8-sig')['Tên'].tolist()
        except:
            return ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]
    return ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

def save_carrier(new_name):
    carriers = load_carriers()
    if new_name not in carriers:
        carriers.append(new_name)
        pd.DataFrame(carriers, columns=['Tên']).to_csv(CARRIER_FILE, index=False, encoding='utf-8-sig')
        return True
    return False

if 'df' not in st.session_state:
    st.session_state.df = load_data()

carrier_list = load_carriers()

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# --- PHẦN 1: CÀI ĐẶT ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    new_carrier = st.text_input("Thêm đơn vị mới")
    if st.button("Lưu đơn vị"):
        if new_carrier:
            if save_carrier(new_carrier):
                st.success("Đã lưu đơn vị mới! ✨")
                st.rerun()

# --- PHẦN 2: NHẬP LIỆU ---
st.subheader("➕ Thêm chuyến mới")
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        date = st.date_input("Ngày giao", datetime.now())
    with col2:
        content = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier = st.selectbox("Đơn vị vận chuyển", carrier_list)
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
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            st.session_state.df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            st.balloons()
            st.rerun()

# --- PHẦN 3: HIỂN THỊ & XÓA ---
st.write("---")
st.subheader("📋 Danh sách chi phí")

if not st.session_state.df.empty:
    df_display = st.session_state.df.copy()
    df_display['Ngày'] = pd.to_datetime(df_display['Ngày'])
    df_display['Tháng_Năm'] = df_display['Ngày'].dt.strftime('%m/%Y')
    
    months = sorted(df_display['Tháng_Năm'].unique(), reverse=True)
    sel_month = st.selectbox("📅 Lọc theo tháng:", months)
    
    month_data = df_display[df_display['Tháng_Năm'] == sel_month].copy()
    
    if not month_data.empty:
        header = st.columns([0.5, 1.5, 3, 2, 1.5, 1])
        header[0].markdown("**STT**")
        header[1].markdown("**Ngày**")
        header[2].markdown("**Nội dung**")
        header[3].markdown("**Đơn vị**")
        header[4].markdown("**Phí (VNĐ)**")
        header[5].markdown("**Xóa**")
        
        st.divider()

        for i, (idx, row) in enumerate(month_data.iterrows(), 1):
            row_cols = st.columns([0.5, 1.5, 3, 2, 1.5, 1])
            row_cols[0].write(f"{i}")
            row_cols[1].write(row['Ngày'].strftime('%d.%m.%Y'))
            row_cols[2].write(row['Nội dung'])
            row_cols[3].write(row['Đơn vị vận chuyển'])
            row_cols[4].write("{:,.0f} đ".format(row['Phí']))
            
            if row_cols[5].button("🗑️", key=f"del_{idx}"):
                st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
                st.session_state.df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                st.rerun()

        total = month_data["Phí"].sum()
        st.info(f"💰 **Tổng cộng tháng {sel_month}: {total:,.0f} VNĐ**")

        # --- XUẤT EXCEL THEO YÊU CẦU ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            export_df = month_data[["Ngày", "Nội dung", "Đơn vị vận chuyển", "Phí"]].copy()
            export_df['Ngày'] = export_df['Ngày'].dt.strftime('%d.%m.%Y')
            export_df.columns = ["Ngày", "Nội dung", "ĐVVC", "Phí"]
            
            # Ghi dữ liệu vào file
            export_df.to_excel(writer, index=False, sheet_name='Báo cáo', startrow=0)
            
            workbook  = writer.book
            worksheet = writer.sheets['Báo cáo']

            # Định dạng
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            content_fmt = workbook.add_format({'border': 1, 'align': 'left'})
            money_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0 "đ"', 'bold': True, 'align': 'right'})
            total_label_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'align': 'center'})
            total_val_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'num_format': '#,##0 "đ"', 'align': 'right'})

            # Kẻ khung cho 30 dòng đầu tiên (hoặc nhiều hơn nếu dữ liệu dài)
            num_rows_to_format = max(30, len(export_df))
            for row_num in range(1, num_rows_to_format + 1):
                worksheet.set_row(row_num, 18) # Chỉnh độ cao dòng cho đẹp
                worksheet.write(row_num, 0, "", content_fmt)
                worksheet.write(row_num, 1, "", content_fmt)
                worksheet.write(row_num, 2, "", content_fmt)
                worksheet.write(row_num, 3, "", content_fmt)

            # Ghi lại dữ liệu thực tế lên trên khung đã kẻ
            for i, row in enumerate(export_df.values):
                worksheet.write(i + 1, 0, row[0], content_fmt)
                worksheet.write(i + 1, 1, row[1], content_fmt)
                worksheet.write(i + 1, 2, row[2], content_fmt)
                worksheet.write(i + 1, 3, row[3], money_fmt)

            # Đẩy dòng Tổng cộng xuống dòng thứ 32 (index 31)
            total_row = 31 
            worksheet.merge_range(total_row, 0, total_row, 2, "TỔNG CỘNG", total_label_fmt)
            worksheet.write(total_row, 3, total, total_val_fmt)

            # Căn chỉnh độ rộng cột
            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:B', 50)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 18)

            # Ghi header
            for col_num, value in enumerate(export_df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)

        excel_data = output.getvalue()
        st.download_button(
            label="📥 Tải file Excel",
            data=excel_data,
            file_name=f"Chi_phi_ship_{sel_month.replace('/', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Chưa có dữ liệu Như ơi! ✨")