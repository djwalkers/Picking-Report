
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Picking Performance Dashboard", layout="wide")

st.title("📦 Picking Performance Dashboard")
st.markdown("Upload your Picking Performance CSV file to begin analysis.")

# File upload
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Sidebar filters
    users = st.sidebar.multiselect("Filter by User", options=df['Username'].unique(), default=df['Username'].unique())
    workstations = st.sidebar.multiselect("Filter by Workstation", options=df['Workstations'].unique(), default=df['Workstations'].unique())

    filtered_df = df[df['Username'].isin(users) & df['Workstations'].isin(workstations)]

    st.markdown("### 📊 Summary Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Source Totes", int(filtered_df['SourceTotes'].sum()))
    col2.metric("Total Destination Totes", int(filtered_df['DestinationTotes'].sum()))
    col3.metric("Total Refills", int(filtered_df['TotalRefills'].sum()))

    st.markdown("### 📈 Performance Over Time")
    time_df = filtered_df.groupby('Date').sum(numeric_only=True).reset_index()
    fig_time = px.line(time_df, x='Date', y=['SourceTotes', 'DestinationTotes', 'TotalRefills'], title='Operational Totals Over Time')
    st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("### 👤 Performance by User")
    user_df = filtered_df.groupby('Username').sum(numeric_only=True).reset_index()
    fig_user = px.bar(user_df, x='Username', y=['SourceTotes', 'DestinationTotes', 'TotalRefills'], barmode='group', title='Operations per User')
    st.plotly_chart(fig_user, use_container_width=True)

    st.markdown("### 🛠️ Performance by Workstation")
    ws_df = filtered_df.groupby('Workstations').sum(numeric_only=True).reset_index()
    fig_ws = px.bar(ws_df, x='Workstations', y=['SourceTotes', 'DestinationTotes', 'TotalRefills'], barmode='group', title='Operations per Workstation')
    st.plotly_chart(fig_ws, use_container_width=True)

    st.markdown("### ⚙️ Efficiency Score")
    filtered_df['Efficiency'] = filtered_df['TotalRefills'] / (filtered_df['SourceTotes'] + filtered_df['DestinationTotes'])
    eff_df = filtered_df.groupby('Username')['Efficiency'].mean().reset_index()
    fig_eff = px.bar(eff_df, x='Username', y='Efficiency', title='Average Efficiency per User')
    st.plotly_chart(fig_eff, use_container_width=True)

    # Download filtered data
    output = BytesIO()
    filtered_df.to_csv(output, index=False)
    st.download_button("Download Filtered CSV", data=output.getvalue(), file_name="filtered_picking_data.csv", mime="text/csv")

else:
    st.info("Please upload a CSV file to begin.")
