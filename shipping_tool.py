import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def get_conn():
    try:
        # Lấy dữ liệu từ Secrets
        s = st.secrets
        # Xử lý ký tự xuống dòng cho private_key để tránh lỗi PEM file
        pk = s["private_key"].replace("\\n", "\n")
        
        creds = {
            "type": "service_account",
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": pk,
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        
        # Kết nối tới Google Sheets
        gc = gspread.service_account_from_dict(creds)
        # ID file của Như: 1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg
        sh = gc.open_by_key("1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg")
        
        # Lấy trang tính có tên "Trang tinh1" như trong hình bạn gửi
        return sh.worksheet("Trang tinh1"), None
    except Exception as e:
        return None, str(e)

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# Thực hiện kết nối
ws, err = get_conn()

if err:
    st.error(f"❌ Kết nối thất bại. Lỗi từ hệ thống: {err}")
    st.info("Như kiểm tra xem đã chia sẻ file Sheets cho email service account chưa nhé!")
else:
    # Form nhập liệu
    with st.form("nhap_lieu", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        ngay = c1.date_input("Ngày tháng năm", datetime.now())
        noidung = c2.text_input("Nội dung (Giao hàng cho ai/cái gì...)")
        donvi = c3.selectbox("Đơn vị vận chuyển", ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦", "Khác"])
        phi = c3.number_input("Phí vận chuyển (VNĐ)", min_value=0, step=1000)
        
        submit = st.form_submit_button("💾 Lưu thông tin")
        
        if submit:
            if noidung:
                try:
                    # Ghi dữ liệu vào Sheets
                    ws.append_row([ngay.strftime('%d/%m/%Y'), noidung, donvi, phi])
                    st.success("Đã lưu xong vào Google Sheets! ✅")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi lưu dữ liệu: {e}")
            else:
                st.warning("Như chưa nhập nội dung giao hàng kìa!")

    # Hiển thị bảng dữ liệu bên dưới (Tùy chọn)
    st.write("---")
    st.subheader("📋 Lịch sử giao hàng gần đây")
    try:
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu nào được ghi.")
    except:
        pass