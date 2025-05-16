# NOTE: set_page_config must be the very first Streamlit command
import streamlit as st
st.set_page_config(page_title="Picking Performance Dashboard", layout="wide")

import pandas as pd
import plotly.express as px
from io import BytesIO
from PIL import Image

# --- THEME: ONLY DARK/BRANDED ---
bg_color = "#DA362C"
text_color = "white"
chart_colors = ["#FFFFFF", "#FFD700", "#1E90FF"]

# Styling injection
st.markdown(f"""
    <style>
        .stApp, .block-container, header, footer, .css-18ni7ap, .css-1d391kg, .css-1v0mbdj, .css-6qob1r, .st-emotion-cache-1v0mbdj {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
        }}
        .css-1v0mbdj .css-1cpxqw2 {{
            background-color: {bg_color} !important;
        }}
        h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown, .stTextInput > div > div > input {{
            color: {text_color} !important;
        }}
    </style>
""", unsafe_allow_html=True)

# Display logo
logo = Image.open("The Roc.png")
st.image(logo, width=200)

st.title("\U0001F4E6 Picking Performance Dashboard")
st.markdown("Upload your Picking Performance CSV file to begin analysis.")

# File upload
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Clean column names and convert data types
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df['SourceTotes'] = pd.to_numeric(df['SourceTotes'], errors='coerce')
    df['DestinationTotes'] = pd.to_numeric(df['DestinationTotes'], errors='coerce')
    df['TotalRefills'] = pd.to_numeric(df['TotalRefills'], errors='coerce')

    # Sidebar filters
    st.sidebar.header("Filters")
    users = st.sidebar.multiselect("Filter by User", options=df['Username'].dropna().unique(), default=df['Username'].dropna().unique())
    workstations = st.sidebar.multiselect("Filter by Workstation", options=df['Workstations'].dropna().unique(), default=df['Workstations'].dropna().unique())
    min_date, max_date = df['Date'].min(), df['Date'].max()
    date_range = st.sidebar.date_input(
        "Select Date Range (DD/MM/YYYY)",
        [min_date.date(), max_date.date()],
        min_value=min_date.date(),
        max_value=max_date.date(),
        format="DD/MM/YYYY"
    )

    metrics_to_show = st.sidebar.multiselect(
        "Select Metrics to Display in Charts",
        options=["SourceTotes", "DestinationTotes", "TotalRefills"],
        default=["SourceTotes", "DestinationTotes", "TotalRefills"]
    )

    filtered_df = df[
        (df['Username'].isin(users)) &
        (df['Workstations'].isin(workstations)) &
        (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
    ]

    st.markdown("### \U0001F4CA Summary Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Source Totes", int(filtered_df['SourceTotes'].sum()))
    col2.metric("Total Destination Totes", int(filtered_df['DestinationTotes'].sum()))
    col3.metric("Total Refills", int(filtered_df['TotalRefills'].sum()))
    # Best average performer
    best_user = filtered_df.copy()
    best_user['Efficiency'] = best_user['TotalRefills'] / (best_user['SourceTotes'] + best_user['DestinationTotes'])
    best_avg = best_user.groupby('Username')['Efficiency'].mean().reset_index().sort_values(by='Efficiency', ascending=False).iloc[0]
    col4.markdown(f"<h6>🏆 Top Efficiency</h6><p style='font-size:14px'>{best_avg['Username']}<br>{best_avg['Efficiency']:.2f}</p>", unsafe_allow_html=True)
    worst_avg = best_user.groupby('Username')['Efficiency'].mean().reset_index().sort_values(by='Efficiency', ascending=True).iloc[0]
    col5.markdown(f"<h6>🔻 Lowest Efficiency</h6><p style='font-size:14px'>{worst_avg['Username']}<br>{worst_avg['Efficiency']:.2f}</p>", unsafe_allow_html=True)

    st.markdown("### \U0001F4C8 Performance Over Time")
    time_df = filtered_df.groupby('Date').sum(numeric_only=True).reset_index()
    if metrics_to_show:
        fig_time = px.line(
            time_df, x='Date', y=metrics_to_show, title='Operational Totals Over Time',
            color_discrete_sequence=chart_colors
        )
        # Add value labels to each trace (one for each metric)
        for trace in fig_time.data:
            trace.update(mode='lines+markers+text', text=[f"{y:.0f}" for y in trace.y], textposition='top center')
        st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("### \U0001F464 Performance by User")
    user_df = filtered_df.groupby('Username').sum(numeric_only=True).reset_index()
    user_df = user_df[user_df[metrics_to_show[0]] > 0]
    user_df = user_df.sort_values(by=metrics_to_show[0], ascending=False)
    fig_user = px.bar(
        user_df,
        x='Username', y=metrics_to_show[0], color='Username',
        title='Total Operations per User',
        color_discrete_sequence=chart_colors, text=metrics_to_show[0]
    )
    fig_user.update_traces(textposition='outside')
    st.plotly_chart(fig_user, use_container_width=True)

    st.markdown("### \U0001F6E0️ Performance by Workstation")
    ws_df = filtered_df.groupby('Workstations').sum(numeric_only=True).reset_index()

    # Only proceed if there's at least one valid metric in ws_df and it's not all zeros
    valid_metrics = [metric for metric in metrics_to_show if metric in ws_df.columns and ws_df[metric].sum() > 0]
    if valid_metrics:
        ws_df = ws_df[ws_df[valid_metrics[0]] > 0]
        ws_df = ws_df.sort_values(by=valid_metrics[0], ascending=False)
        if len(valid_metrics) == 1:
            fig_ws = px.bar(
                ws_df, x='Workstations', y=valid_metrics[0], barmode='group',
                title='Operations per Workstation', color_discrete_sequence=chart_colors,
                text=valid_metrics[0]
            )
            fig_ws.update_traces(textposition='outside')
        else:
            fig_ws = px.bar(
                ws_df, x='Workstations', y=valid_metrics, barmode='group',
                title='Operations per Workstation', color_discrete_sequence=chart_colors,
                text=valid_metrics
            )
            fig_ws.update_traces(textposition='outside')
        st.plotly_chart(fig_ws, use_container_width=True)
    else:
        st.info("No data available for the selected metrics in the current filters.")

    st.markdown("### \u2699\ufe0f Efficiency Score")
    st.caption("Efficiency = Total Refills / (Source Totes + Destination Totes). This gives a rough measure of how many refills are completed per tote moved.")
    filtered_df['Efficiency'] = filtered_df['TotalRefills'] / (filtered_df['SourceTotes'] + filtered_df['DestinationTotes'])
    eff_df = filtered_df.groupby('Username')['Efficiency'].mean().reset_index()
    eff_df = eff_df[eff_df['Efficiency'] > 0]
    eff_df = eff_df.sort_values(by='Efficiency', ascending=False)
    fig_eff = px.bar(
        eff_df, x='Username', y='Efficiency', title='Average Efficiency per User',
        color_discrete_sequence=chart_colors, text='Efficiency'
    )
    fig_eff.update_traces(textposition='outside')
    st.plotly_chart(fig_eff, use_container_width=True)

    output = BytesIO()
    filtered_df.to_csv(output, index=False)
    st.download_button("Download Filtered CSV", data=output.getvalue(), file_name="filtered_picking_data.csv", mime="text/csv")
else:
    st.info("Please upload a CSV file to begin.")

