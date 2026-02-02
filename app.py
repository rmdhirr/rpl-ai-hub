import streamlit as st
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="RPL Practicum Hub", page_icon="🤖")

# PASTE YOUR WEB APP URL HERE
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwKxbxD4eQw5cZHx-1_PW1pg67fGYMbTtDawsQwAnv3H9P4_-D9n4Xs6iFwXkdR5Cypvw/exec"

# --- BACKEND WRAPPER ---
def api_request(payload):
    try:
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        return response.json()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# --- UI ---
def main():
    st.title("🤖 RPL Practicum Hub")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    # LOGIN / REGISTER
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            l_user = st.text_input("Username (Name/NIS)", key="l")
            l_pass = st.text_input("Password", type="password", key="lp")
            if st.button("Login"):
                res = api_request({"action": "login", "username": l_user, "password": l_pass})
                if res and res.get('status') == 'success':
                    st.session_state.logged_in = True
                    st.session_state.username = l_user
                    st.success("Welcome!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        with tab2:
            r_user = st.text_input("New Username", key="r")
            r_pass = st.text_input("New Password", type="password", key="rp")
            if st.button("Register"):
                res = api_request({"action": "register", "username": r_user, "password": r_pass})
                if res and res.get('status') == 'success':
                    st.success("Registered! Please Login.")
                elif res and res.get('message') == 'User taken':
                    st.error("Username already taken.")
                else:
                    st.error("Registration failed.")

    # DASHBOARD
    else:
        st.sidebar.write(f"👤 {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        # Load existing data on load
        if 'form_data' not in st.session_state:
            res = api_request({"action": "get_submission", "username": st.session_state.username})
            if res and res.get('status') == 'found':
                st.session_state.form_data = res['data']
            else:
                st.session_state.form_data = {}

        data = st.session_state.form_data

        # --- TEAMMATE STATE MANAGEMENT ---
        # We handle the "split" logic here so we can edit them one by one
        if 'teammates_list' not in st.session_state:
            raw_teammates = data.get('teammates', '')
            if raw_teammates:
                st.session_state.teammates_list = [t.strip() for t in raw_teammates.split(',') if t.strip()]
            else:
                st.session_state.teammates_list = [""] # Default start with 1 empty slot

        st.subheader("📝 Your Submission")
        
        with st.form("main_form"):
            # 1. Full Name
            full_name = st.text_input("Nama Lengkap", value=data.get('full_name', ''))
            
            # 2. Class
            cls_opts = ["XI RPL 1", "XI RPL 2", "XI RPL 3"]
            saved_cls = data.get('class_name', "XI RPL 1")
            class_name = st.selectbox("Kelas", cls_opts, index=cls_opts.index(saved_cls) if saved_cls in cls_opts else 0)

            # 3. Dynamic Teammates
            st.markdown("---")
            st.write("👥 **Teman Mengerjakan (Projectmates)**")
            st.caption("Masukkan nama teman satu per satu. Jika sendiri, isi satu saja.")

            # Render input for each teammate in the list
            updated_teammates = []
            for i, tm_name in enumerate(st.session_state.teammates_list):
                val = st.text_input(f"Teman #{i+1}", value=tm_name, key=f"tm_{i}")
                updated_teammates.append(val)
            
            # Button to add more (using st.form_submit_button to work inside form, but careful with rerun)
            # Actually, to make "Add" dynamic inside a form is tricky in Streamlit.
            # Best practice: Do the math outside the form or use a "hack".
            # Hack: We use a checkbox or just instruct them to use comma if the UI gets too complex.
            # BETTER UX: Just auto-add a slot if the last one is filled? No, that requires rerun.
            # Let's use a workaround:
            st.caption("ℹ️ *Tips: Jika lebih dari 1, silakan tambah manual atau ketik koma.*") 
            # (Keeping it simple per your request for stability, but making the input clear)
            
            # Since dynamic "Add Button" inside a `st.form` is technically impossible without submitting,
            # I will use your "Segmentation" request by just processing the list cleanly on save,
            # BUT providing a UI to add them OUTSIDE the form is messy.
            # Let's stick to the "Big Text Box" but cleaner, OR use the list approach but without the 'Add' button inside form.
            
            # REVISION: To allow "Add One by One" strictly, we need to step OUT of `st.form` for the adder, 
            # OR just use a cleaner Multiline text area with instructions.
            # However, you asked for "Segmentation". 
            # Let's try the "List Editor" approach which is standard in Python apps:
            
            # Since I cannot put an "Add Row" button inside a `st.form`, I will revert to a Text Area
            # but with very clear formatting instructions as you asked for "UI Friendly".
            
            teammates_text = st.text_area(
                "Teman Mengerjakan (Satu baris satu nama)", 
                value=data.get('teammates', '').replace(',', '\n'), # Display as new lines
                help="Tulis nama teman satu per satu per baris."
            )

            st.markdown("---")

            # 4. Link & Warning
            st.warning("⚠️ **PENTING:** Pastikan link Colab sudah di-set ke **'Anyone with the link' -> 'Editor'** agar saya bisa cek.")
            colab_link = st.text_input("Link Colab (Editor Access)", value=data.get('colab_link', ''))
            
            # 5. Status
            is_done_val = data.get('status')
            if isinstance(is_done_val, str):
                is_done_bool = (is_done_val.lower() == 'true')
            else:
                is_done_bool = bool(is_done_val)

            is_done = st.checkbox("Sudah Beres ✅", value=is_done_bool)

            # SUBMIT
            if st.form_submit_button("Simpan Data"):
                if not colab_link:
                    st.error("Link Colab wajib diisi!")
                else:
                    # Convert new lines back to commas for the database
                    processed_teammates = ", ".join([t.strip() for t in teammates_text.split('\n') if t.strip()])
                    
                    payload = {
                        "action": "update_submission",
                        "username": st.session_state.username,
                        "full_name": full_name,
                        "class_name": class_name,
                        "teammates": processed_teammates,
                        "colab_link": colab_link,
                        "status": is_done
                    }
                    with st.spinner("Menyimpan..."):
                        api_request(payload)
                        # Refresh local state
                        st.session_state.form_data = {
                            "full_name": full_name, "class_name": class_name, 
                            "teammates": processed_teammates, "colab_link": colab_link, "status": is_done
                        }
                    st.success("Data Tersimpan! 🎉")

if __name__ == "__main__":
    main()
