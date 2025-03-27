import pandas as pd
import streamlit as st
import io

st.set_page_config(page_title="LinkedIn Prospect Splitter", layout="centered")
st.title("LinkedIn Daily Prospect Splitter")

st.markdown("""
Upload your daily CSV file with 80-100 prospects. The app will:
1. Categorize by job title into PM, OPEX/CI, and OPS.
2. Split each group equally among 5 LinkedIn accounts: Arun, Assaf, Chen, Leigh, Meirav.
3. Provide 15 downloadable CSVs.
""")

uploaded_file = st.file_uploader("Upload CSV file", type="csv")

accounts = ["arun", "assaf", "chen", "leigh", "meirav"]

def categorize(title):
    title = str(title).lower()
    if any(keyword in title for keyword in ["plant manager", "factory manager", "site manager"]):
        return "pm"
    elif any(keyword in title for keyword in ["opex", "ci", "operational excellence", "continuous improvement", "excellence"]):
        return "opex ci"
    else:
        return "ops"

def split_and_prepare(df):
    split_files = {}
    for group in df['group'].unique():
        group_df = df[df['group'] == group].reset_index(drop=True)
        chunks = [group_df[i::5] for i in range(5)]
        for i, account in enumerate(accounts):
            filename = f"{group} - {account}.csv"
            split_files[filename] = chunks[i].drop(columns=['group'])
    return split_files

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'Job title' not in df.columns:
        st.error("CSV must have a 'Job title' column.")
    else:
        df['group'] = df['Job title'].apply(categorize)
        output_files = split_and_prepare(df)

        st.success("Files processed! Download your 15 split files below:")
        for filename, data in output_files.items():
            buffer = io.BytesIO()
            data.to_csv(buffer, index=False)
            st.download_button(label=f"Download {filename}", data=buffer.getvalue(), file_name=filename, mime="text/csv")
