import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# =========================
# KẾT NỐI GOOGLE SHEETS
# =========================
@st.cache_resource
def get_conn():
    try:
        s = st.secrets

        creds_dict = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": s["private_key"],
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }

        st.write("✅ Đã đọc secrets")

        gc = gspread.service_account_from_dict(creds_dict)

        st.write("✅ Đã xác thực Google")

        sh = gc.open_by_key("1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg")

        st.write("✅ Đã mở Google Sheet")

        ws = sh.sheet1

        st.write("✅ Đã kết nối worksheet")

        return ws

    except Exception as e:
        st.exception(e)
        return None


# =========================
# GIAO DIỆN
# =========================
st.set_page_config(page_title="Quản Lý Ship", layout="wide")

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# =========================
# DANH SÁCH ĐƠN VỊ
# =========================
if "ds_donvi" not in st.session_state:
    st.session_state.ds_donvi = [
        "Ahamove 🛵",
        "Grab 🚗",
        "Lalamove 🚛",
        "GHTK 📦"
    ]

with st.sidebar:
    st.header("⚙️ Cài đặt")

    moi = st.text_input("Thêm đơn vị vận chuyển mới")

    if st.button("Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.success(f"Đã thêm {moi}")
            st.rerun()

# =========================
# KẾT NỐI SHEET
# =========================
ws = get_conn()

if ws is None:
    st.stop()

# =========================
# FORM NHẬP LIỆU
# =========================
with st.form("nhap_lieu", clear_on_submit=True):

    c1, c2, c3 = st.columns([1, 2, 1])

    ngay = c1.date_input("Ngày tháng năm", datetime.now())

    noidung = c2.text_input(
        "Nội dung",
        placeholder="Ví dụ: Giao máy bơm cho khách A"
    )

    donvi = c3.selectbox(
        "Đơn vị vận chuyển",
        st.session_state.ds_donvi
    )

    phi = c3.number_input(
        "Phí (VNĐ)",
        min_value=0,
        step=1000
    )

    submit = st.form_submit_button("💾 Lưu thông tin")

    if submit:

        if not noidung:
            st.warning("Vui lòng nhập nội dung.")
        else:
            try:

                ws.append_row([
                    ngay.strftime('%d/%m/%Y'),
                    noidung,
                    donvi,
                    phi
                ])

                st.success("Đã lưu thành công! ✅")
                st.balloons()

            except Exception as e:
                st.error(f"Lỗi lưu dữ liệu: {e}")

# =========================
# HIỂN THỊ DỮ LIỆU
# =========================
st.divider()

try:

    data = ws.get_all_values()

    if len(data) == 0:

        st.info("Sheet đang trống.")

    else:

        # Nếu sheet chưa có header
        if data[0] != ['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)']:

            ws.insert_row(
                ['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)'],
                1
            )

            data = ws.get_all_values()

        df = pd.DataFrame(data[1:], columns=data[0])

        # Đổi kiểu dữ liệu
        df['Phí (VNĐ)'] = pd.to_numeric(
            df['Phí (VNĐ)'],
            errors='coerce'
        ).fillna(0)

        df['Ngày'] = pd.to_datetime(
            df['Ngày'],
            format='%d/%m/%Y',
            errors='coerce'
        )

        # Chọn tháng
        thang_list = sorted(
            df['Ngày'].dt.strftime('%m/%Y').dropna().unique(),
            reverse=True
        )

        if len(thang_list) > 0:

            thang_chon = st.selectbox(
                "📅 Chọn tháng",
                thang_list
            )

            df_filtered = df[
                df['Ngày'].dt.strftime('%m/%Y') == thang_chon
            ]

            tong = df_filtered['Phí (VNĐ)'].sum()

            c1, c2 = st.columns([3, 1])

            c1.subheader(f"📋 Danh sách tháng {thang_chon}")

            c2.metric(
                "Tổng chi phí",
                f"{tong:,.0f} VNĐ"
            )

            st.dataframe(
                df_filtered,
                use_container_width=True,
                hide_index=True
            )

            csv = df_filtered.to_csv(
                index=False
            ).encode('utf-8-sig')

            st.download_button(
                "📥 Tải báo cáo CSV",
                csv,
                f"bao_cao_{thang_chon}.csv",
                "text/csv"
            )

        else:
            st.info("Chưa có dữ liệu.")

except Exception as e:
    st.error(f"Lỗi hiển thị dữ liệu: {e}")
