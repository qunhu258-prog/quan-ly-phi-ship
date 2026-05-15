import streamlit as st
import gspread
from datetime import datetime  # Thêm dòng này để sửa lỗi image_235062.png

def get_conn():
    try:
        # Lấy dữ liệu trực tiếp từ Secrets (không dùng [gcp_service_account])
        s = st.secrets
        creds_dict = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": s["private_key"],
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        gc = gspread.service_account_from_dict(creds_dict)
        # ID file Sheets của Như từ hình image_2345a2.png
        sh = gc.open_by_key("1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg")
        return sh.get_worksheet(0), None
    except Exception as e:
        return None, str(e)

ws, err = get_conn()

if err:
    st.error(f"Lỗi kết nối: {err}")
else:
    st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# --- SIDEBAR QUẢN LÝ ĐƠN VỊ ---
if 'ds_donvi' not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

with st.sidebar:
    st.header("⚙️ Cài đặt")
    moi = st.text_input("Thêm đơn vị vận chuyển mới")
    if st.button("Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.success(f"Đã thêm {moi}")
            st.rerun()

# --- GIAO DIỆN NHẬP LIỆU ---
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

with st.form("nhap_lieu", clear_on_submit=True):
    c1, c2, c3 = st.columns([1, 2, 1])
    ng = c1.date_input("Ngày tháng năm", datetime.now())
    nd = c2.text_input("Nội dung (Ví dụ: Giao máy bơm cho khách A)")
    dv = c3.selectbox("Đơn vị vận chuyển", st.session_state.ds_donvi)
    t = c3.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu thông tin"):
        if not nd:
            st.error("Như chưa nhập nội dung kìa!")
        else:
            ws, err = get_conn()
            if ws:
                # Ghi vào Sheets: Ngày, Nội dung, Đơn vị, Phí
                ws.append_row([ng.strftime('%d/%m/%Y'), nd, dv, t])
                st.success("Đã lưu vào Sheets thành công! ✅")
                st.balloons()
            else:
                st.error(f"Lỗi kết nối: {err}")

st.write("---")

# --- HIỂN THỊ DỮ LIỆU ---
ws, err = get_conn()
if ws:
    try:
        # Lấy toàn bộ dữ liệu
        data = ws.get_all_values()
        if len(data) > 1: # Có dữ liệu (trừ hàng tiêu đề)
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Chuyển cột Phí sang dạng số để tính tổng
            df['Phí (VNĐ)'] = pd.to_numeric(df['Phí (VNĐ)'], errors='coerce').fillna(0)
            
            # Bộ lọc theo tháng
            df['Ngày'] = pd.to_datetime(df['Ngày'], format='%d/%m/%Y', errors='coerce')
            thang_chon = st.selectbox("Chọn tháng để xem", 
                                     options=sorted(df['Ngày'].dt.strftime('%m/%Y').unique(), reverse=True))
            
            df_filtered = df[df['Ngày'].dt.strftime('%m/%Y') == thang_chon]
            
            # Tính tổng
            tong = df_filtered['Phí (VNĐ)'].sum()
            
            c_a, c_b = st.columns([3, 1])
            c_a.subheader(f"📋 Danh sách tháng {thang_chon}")
            c_b.metric("Tổng chi phí", f"{tong:,.0f} VNĐ")
            
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
            
            # Xuất file
            csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Tải file báo cáo tháng này", csv, f"bao_cao_{thang_chon}.csv", "text/csv")
        else:
            st.info("Chưa có dữ liệu nào được lưu.")
    except Exception as e:
        st.error(f"Lỗi hiển thị bảng: {e}")
else:
    st.error(f"Kết nối thất bại. Lỗi từ hệ thống: {err}")