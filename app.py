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

# --- CHART STYLE FUNCTION ---
def style_chart(fig):
    fig.update_layout(
        font=dict(family="Segoe UI, Arial", size=16, color="#FFF"),
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="center",
            x=0.5,
            font=dict(size=14, color="#FFF"),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=14, color="#FFF"),
            titlefont=dict(size=16, color="#FFF"),
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(255,255,255,0.1)",
            tickfont=dict(size=14, color="#FFF"),
            titlefont=dict(size=16, color="#FFF"),
            zeroline=False,
        ),
        margin=dict(t=60, b=50, l=50, r=30),
    )
    return fig

# Display logo
logo = Image.open("The Roc.png")
st.image(logo, width=200)

st.title("📦 Picking Performance Dashboard")
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

    # --- Summary Metrics ---
    st.markdown("### 📊 Summary Metrics")
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

    # --- Additional High-Level Metrics ---
    st.markdown("### 🏅 High-Level Metrics")

    # Top 3 Users by Refills
    top3_users = (
        filtered_df.groupby('Username')['TotalRefills']
        .sum()
        .sort_values(ascending=False)
        .head(3)
        .reset_index()
    )
    st.markdown("#### Top 3 Users by Refills")
    for idx, row in top3_users.iterrows():
        st.write(f"{idx+1}. {row['Username']}: {int(row['TotalRefills'])} refills")

    # Most Active Workstation
    most_active_ws = filtered_df.groupby('Workstations')['TotalRefills'].sum()
    if not most_active_ws.empty:
        ws_name = most_active_ws.idxmax()
        ws_count = most_active_ws.max()
        st.metric("Most Active Workstation", f"{ws_name} ({int(ws_count)} refills)")

    # Average Totes per User
    if not filtered_df.empty:
        avg_totes_per_user = (
            filtered_df.groupby('Username')[['SourceTotes', 'DestinationTotes']]
            .sum()
            .sum(axis=1)
            .mean()
            .round(0)
        )
        st.metric("Avg Totes per User", int(avg_totes_per_user))

    # Day with Most Operations
    daily_totals = filtered_df.groupby('Date')[['SourceTotes','DestinationTotes','TotalRefills']].sum()
    if not daily_totals.empty:
        best_day = daily_totals['TotalRefills'].idxmax()
        best_total = daily_totals['TotalRefills'].max()
        st.metric("Day with Most Refills", f"{best_day.date()} ({int(best_total)} refills)")

    # --- High-Level Summary Table ---
    st.markdown("### 📋 High-Level Summary Table")
    summary_df = pd.DataFrame({
        'Total Source Totes': [filtered_df['SourceTotes'].sum()],
        'Total Destination Totes': [filtered_df['DestinationTotes'].sum()],
        'Total Refills': [filtered_df['TotalRefills'].sum()],
        'Avg Totes/User': [avg_totes_per_user if not filtered_df.empty else 0]
    })
    st.dataframe(summary_df)

    # --- Performance Over Time ---
    st.markdown("### 📈 Performance Over Time")
    time_df = filtered_df.groupby('Date').sum(numeric_only=True).reset_index()
    if metrics_to_show:
        fig_time = px.line(
            time_df, x='Date', y=metrics_to_show, title='Operational Totals Over Time',
            color_discrete_sequence=chart_colors
        )
        # Add value labels to each trace (one for each metric)
        for trace in fig_time.data:
            trace.update(mode='lines+markers+text', text=[f"{y:.0f}" for y in trace.y], textposition='top center', textfont_size=16)
        fig_time = style_chart(fig_time)
        st.plotly_chart(fig_time, use_container_width=True)

    # --- Performance by User ---
    st.markdown("### 👤 Performance by User")
    user_df = filtered_df.groupby('Username').sum(numeric_only=True).reset_index()
    user_df = user_df[user_df[metrics_to_show[0]] > 0]
    user_df = user_df.sort_values(by=metrics_to_show[0], ascending=False)
    fig_user = px.bar(
        user_df,
        x='Username', y=metrics_to_show[0], color='Username',
        title='Total Operations per User',
        color_discrete_sequence=chart_colors, text=metrics_to_show[0]
    )
    fig_user.update_traces(textposition='outside', marker_line_width=0, marker_line_color="#333", textfont_size=16)
    fig_user = style_chart(fig_user)
    st.plotly_chart(fig_user, use_container_width=True)

    # --- Performance by Workstation ---
    st.markdown("### 🛠️ Performance by Workstation")
    ws_df = filtered_df.groupby('Workstations').sum(numeric_only=True).reset_index()

    # Only proceed if there's at least one valid metric in ws_df and it's not all zeros
    valid_metrics = [metric for metric in metrics_to_show if metric in ws_df.columns and ws_df[metric].sum() > 0]
    if valid_metrics:
        ws_df = ws_df[ws_df[valid_metrics[0]] > 0]
        if not ws_df.empty:
            ws_df = ws_df.sort_values(by=valid_metrics[0], ascending=False)
            # NO VALUE LABELS FOR THIS CHART TO AVOID ERRORS
            if len(valid_metrics) == 1:
                fig_ws = px.bar(
                    ws_df, x='Workstations', y=valid_metrics[0], barmode='group',
                    title='Operations per Workstation', color_discrete_sequence=chart_colors
                )
            else:
                fig_ws = px.bar(
                    ws_df, x='Workstations', y=valid_metrics, barmode='group',
                    title='Operations per Workstation', color_discrete_sequence=chart_colors
                )
            fig_ws.update_traces(marker_line_width=0, marker_line_color="#333")
            fig_ws = style_chart(fig_ws)
            st.plotly_chart(fig_ws, use_container_width=True)
        else:
            st.info("No data available for the selected metrics in the current filters.")
    else:
        st.info("No data available for the selected metrics in the current filters.")

    # --- Efficiency Score ---
    st.markdown("### ⚙️ Efficiency Score")
    st.caption("Efficiency = Total Refills / (Source Totes + Destination Totes). This gives a rough measure of how many refills are completed per tote moved.")
    filtered_df['Efficiency'] = filtered_df['TotalRefills'] / (filtered_df['SourceTotes'] + filtered_df['DestinationTotes'])
    eff_df = filtered_df.groupby('Username')['Efficiency'].mean().reset_index()
    eff_df = eff_df[eff_df['Efficiency'] > 0]
    eff_df = eff_df.sort_values(by='Efficiency', ascending=False)
    eff_df['Efficiency'] = eff_df['Efficiency'].round(0)  # round to whole number
    fig_eff = px.bar(
        eff_df, x='Username', y='Efficiency', title='Average Efficiency per User',
        color_discrete_sequence=chart_colors, text='Efficiency'
    )
    fig_eff.update_traces(texttemplate='%{text:.0f}', textposition='outside', marker_line_width=0, marker_line_color="#333", textfont_size=16)
    fig_eff = style_chart(fig_eff)
    st.plotly_chart(fig_eff, use_container_width=True)

    # --- Download filtered data ---
    output = BytesIO()
    filtered_df.to_csv(output, index=False)
    st.download_button("Download Filtered CSV", data=output.getvalue(), file_name="filtered_picking_data.csv", mime="text/csv")
else:
    st.info("Please upload a CSV file to begin.")

