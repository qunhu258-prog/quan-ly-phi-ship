import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def get_conn():
    try:
        s = st.secrets
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
        gc = gspread.service_account_from_dict(creds)
        # ID file của Như: 1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg
        sh = gc.open_by_key("1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg")
        
        # Lấy trang tính có tên là "Trang tinh1" như trong hình bạn gửi
        return sh.worksheet("Trang tinh1")
    except Exception as e:
        # Nếu có lỗi, nó sẽ hiện ngay lên màn hình App để Như biết lỗi gì
        st.error(f"Lỗi kết nối cụ thể: {e}")
        return None

ws = get_conn()

# Chỉ khi nào kết nối thành công (ws không phải None) mới hiện Form
if ws:
    with st.form("nhap_lieu", clear_on_submit=True):
        # ... (giữ nguyên phần nội dung form của Như)
        if st.form_submit_button("💾 Lưu thông tin"):
            if nd:
                try:
                    ws.append_row([ng.strftime('%d/%m/%Y'), nd, dv, t])
                    st.success("Đã lưu xong! ✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi ghi dữ liệu: {e}")

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

ws, err = get_conn()

if err:
    # Nếu lỗi, nó sẽ hiện chính xác thông báo từ Google
    st.error(f"Lỗi kết nối: {err}")
else:
    with st.form("nhap_lieu", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        ng = c1.date_input("Ngày", datetime.now())
        nd = c2.text_input("Nội dung giao hàng")
        dv = c3.selectbox("Đơn vị", ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦", "Khác"])
        t = c3.number_input("Phí (VNĐ)", min_value=0, step=1000)
        
        if st.form_submit_button("💾 Lưu thông tin"):
            if nd:
                ws.append_row([ng.strftime('%d/%m/%Y'), nd, dv, t])
                st.success("Đã lưu xong! ✅")
                st.balloons()
                st.rerun()
            else:
                st.warning("Như quên nhập nội dung kìa!")

    st.write("---")
    # Hiển thị dữ liệu
    try:
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
    except:
        st.write("Chưa có dữ liệu.")