import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import bcrypt
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="RPL Practicum Hub", page_icon="🤖", layout="centered")

# --- BACKEND FUNCTIONS ---

def get_data(worksheet_name):
    """Fetches data from a specific worksheet using the new connection."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ttl=0 ensures we don't cache old data; we want fresh data every time
    return conn.read(worksheet=worksheet_name, ttl=0)

def update_data(df, worksheet_name):
    """Writes the updated DataFrame back to the sheet."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet=worksheet_name, data=df)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    # Handle cases where hashed might be empty or malformed
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

# --- FRONTEND UI ---

def main():
    st.title("🤖 RPL Practicum Hub")
    
    # Initialize Session State
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    # --- LOGIN / REGISTER VIEW ---
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login")
            l_user = st.text_input("Username (Name/NIS)", key="l_user")
            l_pass = st.text_input("Password", type="password", key="l_pass")
            
            if st.button("Login", type="primary"):
                df_users = get_data("users")
                
                # Check if user exists
                user_row = df_users[df_users['username'].astype(str) == l_user]
                
                if not user_row.empty:
                    stored_hash = user_row.iloc[0]['password']
                    if check_password(l_pass, stored_hash):
                        st.session_state.logged_in = True
                        st.session_state.username = l_user
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Wrong password.")
                else:
                    st.error("User not found.")

        with tab2:
            st.subheader("New Account")
            r_user = st.text_input("Choose Username", key="r_user")
            r_pass = st.text_input("Choose Password", type="password", key="r_pass")
            r_conf = st.text_input("Confirm Password", type="password", key="r_conf")
            
            if st.button("Register"):
                df_users = get_data("users")
                
                if r_user in df_users['username'].astype(str).values:
                    st.error("Username taken.")
                elif r_pass != r_conf:
                    st.error("Passwords don't match.")
                elif len(r_pass) < 4:
                    st.error("Password too short.")
                else:
                    # Add new user
                    new_user = pd.DataFrame([{
                        "username": r_user, 
                        "password": hash_password(r_pass)
                    }])
                    updated_users = pd.concat([df_users, new_user], ignore_index=True)
                    update_data(updated_users, "users")
                    st.success("Account created! Go to Login.")

    # --- STUDENT DASHBOARD ---
    else:
        st.sidebar.write(f"👤 **{st.session_state.username}**")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        st.markdown("### 📝 My Submission")
        
        # Load Submissions
        df_subs = get_data("submissions")
        
        # Find existing row for this user
        # We ensure username column is string to avoid type mismatches
        user_sub_idx = df_subs.index[df_subs['username'].astype(str) == st.session_state.username].tolist()
        
        existing_data = None
        if user_sub_idx:
            existing_data = df_subs.loc[user_sub_idx[0]]

        with st.form("sub_form"):
            full_name = st.text_input("Full Name", value=existing_data['full_name'] if existing_data is not None else "")
            
            class_opts = ["XI RPL 1", "XI RPL 2", "XI RPL 3"]
            curr_class = existing_data['class_name'] if existing_data is not None and existing_data['class_name'] in class_opts else "XI RPL 1"
            class_name = st.selectbox("Class", class_opts, index=class_opts.index(curr_class))

            teammates = st.text_area("Teammates (Optional)", value=existing_data['teammates'] if existing_data is not None else "")
            
            colab_link = st.text_input("Colab Link", value=existing_data['colab_link'] if existing_data is not None else "")
            
            is_done = st.checkbox("Sudah Beres?", value=(existing_data['status'] == "TRUE") if existing_data is not None else False)

            if st.form_submit_button("Save"):
                new_row = {
                    "username": st.session_state.username,
                    "full_name": full_name,
                    "class_name": class_name,
                    "teammates": teammates,
                    "colab_link": colab_link,
                    "status": "TRUE" if is_done else "FALSE",
                    "last_updated": str(datetime.now())
                }
                
                if user_sub_idx:
                    # Update existing row
                    # We have to update the specific row in the dataframe
                    df_subs.loc[user_sub_idx[0]] = new_row
                else:
                    # Append new row
                    df_subs = pd.concat([df_subs, pd.DataFrame([new_row])], ignore_index=True)
                
                update_data(df_subs, "submissions")
                st.success("Saved!")

if __name__ == "__main__":
    main()
