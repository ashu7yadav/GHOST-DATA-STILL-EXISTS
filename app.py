from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Deletion Detective AI", page_icon="🕵️", layout="wide")
st.title("Deletion Detective AI")

base_dir = Path(__file__).resolve().parent
output_path = base_dir / "output.csv"

if output_path.exists():
    df = pd.read_csv(output_path)
    st.metric("Total requests", len(df))
    st.metric("Complete", int((df["deletion_status"] == "COMPLETE").sum()))
    st.metric("Incomplete", int((df["deletion_status"] == "INCOMPLETE").sum()))
    st.metric("Not applicable", int((df["deletion_status"] == "NOT_APPLICABLE").sum()))
    st.dataframe(df.head(50), use_container_width=True)
else:
    st.warning("Run the pipeline first to generate output.csv.")
