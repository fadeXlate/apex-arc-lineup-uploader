import streamlit as st
import pandas as pd
import requests
from io import StringIO

API_URL = "https://your-backend-url.onrender.com/upload-lineup"  # Replace this after deployment
JWT_TOKEN = "valid-token"  # Replace with secure token in production

st.title("Apex Arc Lineup Uploader")

uploaded_file = st.file_uploader("Upload your lineup CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        st.error("Invalid CSV file.")
        st.stop()

    required_cols = {"player", "team"}
    if not required_cols.issubset(set(df.columns.str.lower())):
        st.error(f"CSV missing required columns: {required_cols}")
        st.stop()

    st.write("✅ Preview of your lineup:")
    st.dataframe(df)

    if st.button("Confirm Lineup and Get Predictions"):
        with st.spinner("Validating lineup and fetching predictions..."):
            csv_str = df.to_csv(index=False)
            headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
            files = {"file": ("lineup.csv", csv_str)}
            try:
                resp = requests.post(API_URL, files=files, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    st.success("Lineup validated and predictions received!")
                    st.write("**Validated Lineup:**")
                    st.dataframe(pd.DataFrame(data["lineup"]))
                    st.write("**Predictions:**")
                    st.dataframe(pd.DataFrame(data["predictions"]))
                else:
                    error_detail = resp.json().get("detail", "Unknown error")
                    st.error(f"Validation failed: {error_detail}")
            except Exception as e:
                st.error(f"Request failed: {e}")