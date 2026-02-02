import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="RPL Practicum Hub", page_icon="💻", layout="wide")

# ⚠️ PASTE YOUR APPS SCRIPT URL HERE
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxvLt_9VQHv0138YITFw3kIsF3QUYSSWCs0fXXl2RAhpgALh4LBFHmaLmCOOu-s9JA7cg/exec"

# --- BACKEND WRAPPER ---
def api_request(payload):
    try:
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        return response.json()
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

# --- UI ---
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    # ==========================================
    # 🔐 LOGIN / REGISTER SCREEN
    # ==========================================
    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("💻 RPL Practicum Hub")
            st.info("ℹ️ **Perhatian:** Harap ingat Username & Password!")
            
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                l_user = st.text_input("Username", key="l")
                l_pass = st.text_input("Password", type="password", key="lp")
                if st.button("Login", type="primary", use_container_width=True):
                    with st.spinner("Masuk..."):
                        res = api_request({"action": "login", "username": l_user, "password": l_pass})
                        if res and res.get('status') == 'success':
                            st.session_state.logged_in = True
                            st.session_state.username = l_user
                            st.rerun()
                        else:
                            st.error("Salah password/username.")

            with tab2:
                r_user = st.text_input("Buat Username", key="r")
                r_pass = st.text_input("Buat Password", type="password", key="rp")
                if st.button("Register", use_container_width=True):
                    with st.spinner("Mendaftar..."):
                        res = api_request({"action": "register", "username": r_user, "password": r_pass})
                        if res and res.get('status') == 'success':
                            st.success("Berhasil! Silakan Login.")
                        elif res and res.get('message') == 'User taken':
                            st.error("Username sudah dipakai.")
                        else:
                            st.error("Gagal.")

    # ==========================================
    # 🏠 LOGGED IN AREA
    # ==========================================
    else:
        st.sidebar.title("🔧 Menu")
        st.sidebar.write(f"User: **{st.session_state.username}**")
        if st.sidebar.button("Logout", type="primary"):
            st.session_state.logged_in = False
            st.rerun()

        # ------------------------------------------
        # 👑 ADMIN DASHBOARD
        # ------------------------------------------
        if st.session_state.username == "admin": 
            st.title("👑 Admin Dashboard")
            st.markdown("### Rekapitulasi Tugas Siswa")

            if st.button("🔄 Refresh Data"):
                st.rerun()

            with st.spinner("Mengambil data..."):
                res = api_request({"action": "get_all_data"})
            
            if res and res.get('status') == 'success':
                data = res['data']
                if len(data) > 0:
                    df = pd.DataFrame(data)

                    # Metrics
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Siswa", len(df))
                    c2.metric("Sudah Beres", len(df[df['status'] == 'Sudah Mengerjakan']))
                    c3.metric("Belum Beres", len(df[df['status'] != 'Sudah Mengerjakan']))

                    st.markdown("---")
                    
                    # Group by Class
                    classes = ["XI RPL 1", "XI RPL 2", "XI RPL 3"]
                    tabs = st.tabs(classes)

                    for i, cls in enumerate(classes):
                        with tabs[i]:
                            df_class = df[df['class_name'] == cls].copy()
                            if df_class.empty:
                                st.info("Belum ada data.")
                            else:
                                df_disp = df_class[['full_name', 'angkatan', 'colab_filename', 'colab_link', 'status', 'teammates', 'last_updated']]
                                st.data_editor(
                                    df_disp,
                                    column_config={
                                        "full_name": "Nama",
                                        "angkatan": "Angkatan",
                                        "colab_filename": "File",
                                        "colab_link": st.column_config.LinkColumn("Link", display_text="Buka 🔗"),
                                        "status": "Status",
                                        "teammates": "Tim",
                                        "last_updated": "Update"
                                    },
                                    hide_index=True, disabled=True, use_container_width=True
                                )
                else:
                    st.warning("Data kosong.")
            else:
                st.error("Gagal koneksi ke server.")

        # ------------------------------------------
        # 🎓 STUDENT DASHBOARD
        # ------------------------------------------
        else:
            st.title("📝 Form Pengumpulan")
            
            if 'form_data' not in st.session_state:
                with st.spinner("Loading data..."):
                    res = api_request({"action": "get_submission", "username": st.session_state.username})
                    if res and res.get('status') == 'found':
                        st.session_state.form_data = res['data']
                    else:
                        st.session_state.form_data = {}

            data = st.session_state.form_data

            if data.get('colab_link'):
                st.success(f"📂 **File Tersimpan:** [{data.get('colab_filename')}]({data.get('colab_link')})")

            with st.form("student_form"):
                st.subheader("1. Identitas")
                
                # Name (Row 1)
                full_name = st.text_input("Nama Lengkap", value=data.get('full_name', ''))
                
                # Class & Batch (Row 2)
                c_a, c_b = st.columns(2)
                with c_a:
                    cls_opts = ["XI RPL 1", "XI RPL 2", "XI RPL 3"]
                    curr = data.get('class_name', "XI RPL 1")
                    class_name = st.selectbox("Kelas", cls_opts, index=cls_opts.index(curr) if curr in cls_opts else 0)
                
                with c_b:
                    # NEW ANGKATAN DROPDOWN
                    angkatan_opts = ["2025/2026"]
                    curr_angk = data.get('angkatan', "2025/2026")
                    # Safe index check in case we add more years later
                    idx_angk = angkatan_opts.index(curr_angk) if curr_angk in angkatan_opts else 0
                    angkatan = st.selectbox("Tahun Ajaran (Angkatan)", angkatan_opts, index=idx_angk)

                st.caption("👥 **Projectmates (Teman Kelompok)**")
                teammates_text = st.text_area("List nama teman (satu per baris)", value=data.get('teammates', '').replace(',', '\n'), height=68)

                st.markdown("---")
                st.subheader("2. File Praktikum")
                st.warning("⚠️ **Aturan:** Ganti nama file Colab jadi `Praktikum X_Minggu Y_Nama_Kelas` & Set akses ke **Editor**.")
                
                colab_filename = st.text_input("Nama File Colab (Sesuai format)", value=data.get('colab_filename', ''))
                colab_link = st.text_input("Link Colab", value=data.get('colab_link', ''))

                st.markdown("---")
                st.subheader("3. Konfirmasi")
                st.write("❓ **Sudah beres mengerjakan belum?**")
                
                status_opts = ["Belum Mengerjakan", "Sudah Mengerjakan"]
                saved_stat = data.get('status', "Belum Mengerjakan")
                if str(saved_stat).upper() == 'TRUE': saved_stat = "Sudah Mengerjakan"
                
                idx_stat = status_opts.index(saved_stat) if saved_stat in status_opts else 0
                status_input = st.selectbox("Pilih Status:", status_opts, index=idx_stat, label_visibility="collapsed")

                submitted = st.form_submit_button("💾 Simpan Data", type="primary")

                if submitted:
                    if not colab_link or not colab_filename or not full_name:
                        st.error("Mohon lengkapi Nama, Link, dan Nama File.")
                    else:
                        tm = ", ".join([t.strip() for t in teammates_text.split('\n') if t.strip()])
                        payload = {
                            "action": "update_submission",
                            "username": st.session_state.username,
                            "full_name": full_name,
                            "class_name": class_name,
                            "angkatan": angkatan, # NEW PAYLOAD
                            "teammates": tm,
                            "colab_link": colab_link,
                            "colab_filename": colab_filename,
                            "status": status_input
                        }
                        with st.spinner("Menyimpan..."):
                            api_request(payload)
                            st.session_state.form_data = payload
                        st.success("Tersimpan!")
                        st.rerun()

if __name__ == "__main__":
    main()
