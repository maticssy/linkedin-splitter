import pandas as pd
import streamlit as st
import io
import os

st.set_page_config(page_title="LinkedIn Prospect Splitter", layout="centered")
st.title("LinkedIn Daily Prospect Splitter")

st.markdown("""
Upload your daily CSV file with 80-100 prospects. The app will:
1. Categorize by job title into PM, OPEX/CI, and OPS.
2. Split each group equally among 5 LinkedIn accounts: Arun, Assaf, Chen, Leigh, Meirav.
3. Provide 15 downloadable CSVs.
4. Show a summary of the breakdown.
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

def split_and_prepare(df, base_name):
    split_files = {}
    distribution = {account: {"pm": 0, "opex ci": 0, "ops": 0, "total": 0} for account in accounts}
    for group in df['group'].unique():
        group_df = df[df['group'] == group].reset_index(drop=True)
        chunks = [group_df[i::5] for i in range(5)]
        for i, account in enumerate(accounts):
            chunk = chunks[i].drop(columns=['group'])
            filename = f"{base_name} - {group} - {account}.csv"
            split_files[filename] = chunk
            distribution[account][group] += len(chunk)
            distribution[account]["total"] += len(chunk)
    return split_files, distribution

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    base_name = os.path.splitext(uploaded_file.name)[0]  # remove .csv extension

    if 'Job Title' not in df.columns:
        st.error("CSV must have a 'Job Title' column.")
    else:
        df['group'] = df['Job Title'].apply(categorize)
        output_files, distribution = split_and_prepare(df, base_name)

        st.success("Files processed! Download your 15 split files below:")

        st.markdown(f"**Total contacts:** {len(df)}")
        st.markdown("**Group breakdown:**")
        group_counts = df['group'].value_counts()
        for group in ["pm", "opex ci", "ops"]:
            st.markdown(f"- {group.upper()}: {group_counts.get(group, 0)}")

        st.markdown("**Distribution per LinkedIn account:**")
        for account in accounts:
            st.markdown(f"- **{account.capitalize()}**: {distribution[account]['total']} (PM: {distribution[account]['pm']}, OPEX/CI: {distribution[account]['opex ci']}, OPS: {distribution[account]['ops']})")

        for filename, data in output_files.items():
            buffer = io.BytesIO()
            data.to_csv(buffer, index=False)
            st.download_button(label=f"Download {filename}", data=buffer.getvalue(), file_name=filename, mime="text/csv")
