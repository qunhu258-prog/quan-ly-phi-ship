import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Hàm kết nối an toàn
def get_conn():
    try:
        # Lấy thông tin từ Secrets đã cấu hình
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Mở file bằng ID Như đã chia sẻ (image_2528c8.png)
        sh = client.open_by_key("1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg")
        
        # Mở trang tính đầu tiên
        return sh.get_worksheet(0) 
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None

# Gọi hàm kết nối
ws = get_conn()

# Chỉ khi kết nối thành công mới cho phép nhấn nút Lưu
if ws is not None:
    # ... phần code vẽ giao diện (input ngày, nội dung, đơn giá...) của Như ...
    
    if st.button("Lưu thông tin"):
        try:
            # Ghi dữ liệu vào dòng cuối cùng
            ws.append_row([ngay, noi_dung, don_vi, phi])
            st.success("Đã lưu dữ liệu thành công vào Google Sheets!")
            st.balloons()
        except Exception as e:
            st.error(f"Lỗi khi lưu: {e}")
else:
    st.warning("Ứng dụng chưa thể kết nối với dữ liệu. Vui lòng kiểm tra lại quyền chia sẻ file Sheets.")    # Form nhập liệu
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