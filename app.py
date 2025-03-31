import pandas as pd
import streamlit as st
import io
import os
import zipfile
import tempfile
from collections import defaultdict
from datetime import datetime

st.set_page_config(page_title="LinkedIn Prospect Splitter", layout="centered")
st.title("LinkedIn Daily Prospect Splitter")

st.markdown("""
Upload your daily CSV file with 80-100 prospects. The app will:
1. Categorize by job title into PM, OPEX/CI, and OPS.
2. Distribute each group as evenly as possible across 5 LinkedIn accounts.
3. Ensure both fair group splitting AND perfectly balanced totals.
4. Provide 15 downloadable CSVs and a bulk ZIP.
5. Log and display daily upload summary.
""")

uploaded_file = st.file_uploader("Upload CSV file", type="csv")

accounts = ["arun", "assaf", "chen", "leigh", "meirav"]

log_entries = []

def categorize(title):
    title = str(title).lower()
    if any(keyword in title for keyword in ["plant manager", "factory manager", "site manager"]):
        return "pm"
    elif any(keyword in title for keyword in ["opex", "ci", "operational excellence", "continuous improvement", "excellence"]):
        return "opex ci"
    else:
        return "ops"

def assign_chunks_balanced(groups):
    output = {account: [] for account in accounts}
    distribution = defaultdict(lambda: {"pm": 0, "opex ci": 0, "ops": 0, "total": 0})
    rotation_offset = 0

    for group_name, group_df in groups.items():
        group_df = group_df.sample(frac=1).reset_index(drop=True)
        chunks = [[] for _ in range(len(accounts))]
        for i, (_, row) in enumerate(group_df.iterrows()):
            chunks[i % len(accounts)].append(row)

        for i, chunk in enumerate(chunks):
            account = accounts[(i + rotation_offset) % len(accounts)]
            for row in chunk:
                record = row.to_dict()
                output[account].append(record)
                distribution[account][group_name] += 1
                distribution[account]["total"] += 1

        rotation_offset += 1

    return output, distribution

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    base_name = os.path.splitext(uploaded_file.name)[0]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if 'Job Title' not in df.columns:
        st.error("CSV must have a 'Job Title' column.")
    else:
        df['group'] = df['Job Title'].apply(categorize)
        groups = {g: df[df['group'] == g] for g in ['pm', 'opex ci', 'ops']}
        output_map, distribution = assign_chunks_balanced(groups)

        st.success("Files processed! Download your 15 split files below:")

        total_contacts = len(df)
        st.markdown(f"**Total contacts:** {total_contacts}")
        st.markdown("**Group breakdown:**")
        group_counts = df['group'].value_counts()
        for group in ["pm", "opex ci", "ops"]:
            st.markdown(f"- {group.upper()}: {group_counts.get(group, 0)}")

        st.markdown("**Distribution per LinkedIn account:**")
        for account in accounts:
            pm = distribution[account]['pm']
            opex = distribution[account]['opex ci']
            ops = distribution[account]['ops']
            total = distribution[account]['total']
            st.markdown(f"- **{account.capitalize()}**: {total} (PM: {pm}, OPEX/CI: {opex}, OPS: {ops})")

        # Store downloadable files and prepare ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for account, rows in output_map.items():
                output_df = pd.DataFrame(rows).drop(columns=['group'])
                for group in ["pm", "opex ci", "ops"]:
                    group_df = pd.DataFrame([r for r in rows if r["group"] == group])
                    if not group_df.empty:
                        filename = f"{base_name} - {group} - {account}.csv"
                        buffer = io.StringIO()
                        group_df.drop(columns=['group']).to_csv(buffer, index=False)
                        zip_file.writestr(filename, buffer.getvalue())

        zip_buffer.seek(0)
        st.download_button("📦 Download all as ZIP", data=zip_buffer, file_name=f"{base_name}_split_files.zip", mime="application/zip")

        # Display log summary
        st.markdown("---")
        st.markdown("### 📅 Upload Log")
        st.markdown(f"**Date:** {timestamp}")
        st.markdown(f"**File name:** {uploaded_file.name}")
        st.markdown(f"**Total contacts:** {total_contacts}")
        for group in ["pm", "opex ci", "ops"]:
            st.markdown(f"- {group.upper()}: {group_counts.get(group, 0)}")
