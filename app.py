import streamlit as st
st.set_page_config(page_title="Picking Performance Dashboard", layout="wide")

import pandas as pd
import plotly.express as px
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta

bg_color = "#DA362C"
text_color = "white"
chart_colors = ["#FFFFFF", "#FFD700", "#1E90FF"]

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
        .outlier {{
            color: #FFD700 !important;
            background-color: #750000 !important;
            border-radius: 6px;
            padding: 2px 8px;
            font-weight: bold;
            display: inline-block;
        }}
    </style>
""", unsafe_allow_html=True)

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
            title=dict(font=dict(size=16, color="#FFF")),
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(255,255,255,0.1)",
            tickfont=dict(size=14, color="#FFF"),
            title=dict(font=dict(size=16, color="#FFF")),
            zeroline=False,
        ),
        margin=dict(t=60, b=50, l=50, r=30),
    )
    return fig

logo = Image.open("The Roc.png")
st.image(logo, width=200)

st.title("📦 Picking Performance Dashboard")
st.markdown("Upload your Picking Performance CSV file to begin analysis.")

uploaded_file = st.file_uploader("Upload CSV", type="csv")

def assign_shift(dt):
    if pd.isnull(dt):
        return "UNKNOWN"
    hour = dt.hour
    if 6 <= hour < 14:
        return "AM"
    elif 14 <= hour < 22:
        return "PM"
    else:
        return "NIGHT"

def get_date_slicer(min_date, max_date):
    today = pd.Timestamp.today().normalize()
    week_ago = today - pd.Timedelta(days=6)
    month_ago = today - pd.Timedelta(days=29)
    slicer = st.sidebar.radio(
        "Quick Date Slicers",
        options=["Today", "This Week", "This Month", "Custom"],
        index=2 if max_date - min_date > pd.Timedelta(days=7) else 0,
        horizontal=True,
    )
    if slicer == "Today":
        return [today, today]
    elif slicer == "This Week":
        return [week_ago, today]
    elif slicer == "This Month":
        return [month_ago, today]
    else:
        return st.sidebar.date_input(
            "Select Date Range (DD/MM/YYYY)",
            [min_date.date(), max_date.date()],
            min_value=min_date.date(),
            max_value=max_date.date(),
            format="DD/MM/YYYY"
        )

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    df['DateTime'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df['Date'] = df['DateTime'].dt.date
    df['Time'] = df['DateTime'].dt.time
    df['Shift'] = df['DateTime'].apply(assign_shift)
    df['SourceTotes'] = pd.to_numeric(df['SourceTotes'], errors='coerce')
    df['DestinationTotes'] = pd.to_numeric(df['DestinationTotes'], errors='coerce')
    df['TotalRefills'] = pd.to_numeric(df['TotalRefills'], errors='coerce')

    st.sidebar.header("Filters")
    users = st.sidebar.multiselect("Filter by User", options=df['Username'].dropna().unique(), default=df['Username'].dropna().unique())
    workstations = st.sidebar.multiselect("Filter by Workstation", options=df['Workstations'].dropna().unique(), default=df['Workstations'].dropna().unique())
    min_dt, max_dt = df['DateTime'].min(), df['DateTime'].max()
    date_range = get_date_slicer(min_dt, max_dt)
    date_start, date_end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

    metrics_to_show = st.sidebar.multiselect(
        "Select Metrics to Display in Charts",
        options=["SourceTotes", "DestinationTotes", "TotalRefills"],
        default=["SourceTotes", "DestinationTotes", "TotalRefills"]
    )

    filtered_df = df[
        (df['Username'].isin(users)) &
        (df['Workstations'].isin(workstations)) &
        (df['DateTime'] >= date_start) & (df['DateTime'] <= (date_end + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)))
    ]

    # Summary metrics
    st.markdown("### 📊 Summary Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Source Totes", int(filtered_df['SourceTotes'].sum()))
    col2.metric("Total Destination Totes", int(filtered_df['DestinationTotes'].sum()))
    col3.metric("Total Refills", int(filtered_df['TotalRefills'].sum()))
    best_user = filtered_df.copy()
    best_user['Efficiency'] = best_user['TotalRefills'] / (best_user['SourceTotes'] + best_user['DestinationTotes'])
    if not best_user.empty:
        best_avg = best_user.groupby('Username')['Efficiency'].mean().reset_index().sort_values(by='Efficiency', ascending=False).iloc[0]
        worst_avg = best_user.groupby('Username')['Efficiency'].mean().reset_index().sort_values(by='Efficiency', ascending=True).iloc[0]
        col4.markdown(f"<h6>🏆 Top Efficiency</h6><p style='font-size:14px'>{best_avg['Username']}<br>{best_avg['Efficiency']:.2f}</p>", unsafe_allow_html=True)
        col5.markdown(f"<h6>🔻 Lowest Efficiency</h6><p style='font-size:14px'>{worst_avg['Username']}<br>{worst_avg['Efficiency']:.2f}</p>", unsafe_allow_html=True)
    else:
        col4.markdown("-")
        col5.markdown("-")

    st.markdown(f"**Date Range:** {date_start.date()} to {date_end.date()}")

    st.markdown("### ⏰ Per Shift Totals")
    shift_df = filtered_df.groupby(['Shift']).agg({
        'SourceTotes': 'sum',
        'DestinationTotes': 'sum',
        'TotalRefills': 'sum'
    }).reset_index()
    st.dataframe(shift_df.style.format(precision=0), use_container_width=True)

    # Outlier calculation
    user_stats = filtered_df.groupby('Username')[['TotalRefills','SourceTotes','DestinationTotes']].sum().reset_index()
    user_stats['Efficiency'] = user_stats['TotalRefills'] / (user_stats['SourceTotes'] + user_stats['DestinationTotes'])
    mean_eff = user_stats['Efficiency'].mean()
    mean_refills = user_stats['TotalRefills'].mean()
    user_stats['Eff_Outlier'] = user_stats['Efficiency'] < (0.5 * mean_eff)
    user_stats['Refill_Outlier'] = user_stats['TotalRefills'] < (0.5 * mean_refills)
    outlier_users = user_stats[(user_stats['Eff_Outlier']) | (user_stats['Refill_Outlier'])]

    day_stats = filtered_df.groupby('Date')[['TotalRefills','SourceTotes','DestinationTotes']].sum().reset_index()
    day_stats['Efficiency'] = day_stats['TotalRefills'] / (day_stats['SourceTotes'] + day_stats['DestinationTotes'])
    mean_eff_day = day_stats['Efficiency'].mean()
    mean_refills_day = day_stats['TotalRefills'].mean()
    day_stats['Eff_Outlier'] = day_stats['Efficiency'] < (0.5 * mean_eff_day)
    day_stats['Refill_Outlier'] = day_stats['TotalRefills'] < (0.5 * mean_refills_day)
    outlier_days = day_stats[(day_stats['Eff_Outlier']) | (day_stats['Refill_Outlier'])]

    ws_stats = filtered_df.groupby('Workstations')[['TotalRefills','SourceTotes','DestinationTotes']].sum().reset_index()
    ws_stats['Efficiency'] = ws_stats['TotalRefills'] / (ws_stats['SourceTotes'] + ws_stats['DestinationTotes'])
    mean_eff_ws = ws_stats['Efficiency'].mean()
    mean_refills_ws = ws_stats['TotalRefills'].mean()
    ws_stats['Eff_Outlier'] = ws_stats['Efficiency'] < (0.5 * mean_eff_ws)
    ws_stats['Refill_Outlier'] = ws_stats['TotalRefills'] < (0.5 * mean_refills_ws)
    outlier_ws = ws_stats[(ws_stats['Eff_Outlier']) | (ws_stats['Refill_Outlier'])]

    # --- Outliers section (mean always visible and with descriptions) ---
    st.markdown("### ⚠️ Outliers (< 50% of Mean)")

    # User Outliers
    st.markdown(f"""
**User Outliers**  
<small>
Users whose average efficiency or total refills are less than 50% of the group mean. This may indicate consistently underperforming team members.<br>
Mean Efficiency: <b>{mean_eff:.2f}</b>, Mean Refills: <b>{mean_refills:.0f}</b>
</small>
""", unsafe_allow_html=True)
    if not outlier_users.empty:
        for _, row in outlier_users.iterrows():
            st.markdown(
                f"<span class='outlier'>User: {row['Username']} | Efficiency: {row['Efficiency']:.2f} | Refills: {int(row['TotalRefills'])}</span>",
                unsafe_allow_html=True)
    else:
        st.info("No user outliers detected in current filters.")

    # Day Outliers
    st.markdown(f"""
**Day Outliers**  
<small>
Dates with average efficiency or total refills below 50% of the group mean. These may be days with unexpected operational issues or lower throughput.<br>
Mean Efficiency: <b>{mean_eff_day:.2f}</b>, Mean Refills: <b>{mean_refills_day:.0f}</b>
</small>
""", unsafe_allow_html=True)
    if not outlier_days.empty:
        for _, row in outlier_days.iterrows():
            st.markdown(
                f"<span class='outlier'>Day: {row['Date']} | Efficiency: {row['Efficiency']:.2f} | Refills: {int(row['TotalRefills'])}</span>",
                unsafe_allow_html=True)
    else:
        st.info("No day outliers detected in current filters.")

    # Workstation Outliers
    st.markdown(f"""
**Workstation Outliers**  
<small>
Workstations with average efficiency or total refills less than 50% of the mean. This may point to problem areas or underutilized equipment.<br>
Mean Efficiency: <b>{mean_eff_ws:.2f}</b>, Mean Refills: <b>{mean_refills_ws:.0f}</b>
</small>
""", unsafe_allow_html=True)
    if not outlier_ws.empty:
        for _, row in outlier_ws.iterrows():
            st.markdown(
                f"<span class='outlier'>WS: {row['Workstations']} | Efficiency: {row['Efficiency']:.2f} | Refills: {int(row['TotalRefills'])}</span>",
                unsafe_allow_html=True)
    else:
        st.info("No workstation outliers detected in current filters.")

    # --------- Rest of dashboard (unchanged) -----------
    st.markdown("### 📈 Performance Over Time")
    time_df = filtered_df.groupby('Date').sum(numeric_only=True).reset_index()
    valid_time_metrics = []
    for col in metrics_to_show:
        if (
            col in time_df.columns
            and pd.api.types.is_numeric_dtype(time_df[col])
            and time_df[col].notna().sum() > 0
            and (time_df[col].fillna(0) != 0).any()
        ):
            valid_time_metrics.append(col)

    if valid_time_metrics and not time_df.empty:
        fig_time = px.line(
            time_df, x='Date', y=valid_time_metrics, title='Operational Totals Over Time',
            color_discrete_sequence=chart_colors
        )
        for trace in fig_time.data:
            trace.update(mode='lines+markers+text', text=[f"{y:.0f}" for y in trace.y], textposition='top center', textfont_size=16)
        fig_time = style_chart(fig_time)
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("No data available for the selected metrics in the current filters.")

    st.markdown("### ⏲️ Performance by Shift")
    shift_sum_df = filtered_df.groupby('Shift').sum(numeric_only=True).reset_index()
    if not shift_sum_df.empty:
        fig_shift = px.bar(
            shift_sum_df, x='Shift', y=metrics_to_show[0], color='Shift',
            title='Total Operations per Shift',
            color_discrete_sequence=chart_colors, text=metrics_to_show[0]
        )
        fig_shift.update_traces(textposition='outside', marker_line_width=0, marker_line_color="#333", textfont_size=16)
        fig_shift = style_chart(fig_shift)
        st.plotly_chart(fig_shift, use_container_width=True)
    else:
        st.info("No data for shifts in current filters.")

    st.markdown("### 👤 Performance by User")
    user_df = filtered_df.groupby('Username').sum(numeric_only=True).reset_index()
    valid_user_metrics = []
    for col in metrics_to_show:
        if (
            col in user_df.columns
            and pd.api.types.is_numeric_dtype(user_df[col])
            and user_df[col].notna().sum() > 0
            and (user_df[col].fillna(0) != 0).any()
        ):
            valid_user_metrics.append(col)
    if valid_user_metrics and not user_df.empty:
        user_df = user_df[user_df[valid_user_metrics[0]] > 0]
        user_df = user_df.sort_values(by=valid_user_metrics[0], ascending=False)
        fig_user = px.bar(
            user_df,
            x='Username', y=valid_user_metrics[0], color='Username',
            title='Total Operations per User',
            color_discrete_sequence=chart_colors, text=valid_user_metrics[0]
        )
        fig_user.update_traces(textposition='outside', marker_line_width=0, marker_line_color="#333", textfont_size=16)
        fig_user.update_layout(showlegend=False)  # Removes the legend
        fig_user = style_chart(fig_user)
        st.plotly_chart(fig_user, use_container_width=True)
    else:
        st.info("No data available for the selected metrics in the current filters.")

    st.markdown("### 🛠️ Performance by Workstation")
    ws_df = filtered_df.groupby('Workstations').sum(numeric_only=True).reset_index()
    valid_ws_metrics = []
    for col in metrics_to_show:
        if (
            col in ws_df.columns
            and pd.api.types.is_numeric_dtype(ws_df[col])
            and ws_df[col].notna().sum() > 0
            and (ws_df[col].fillna(0) != 0).any()
        ):
            valid_ws_metrics.append(col)
    if valid_ws_metrics and not ws_df.empty:
        ws_df = ws_df[ws_df[valid_ws_metrics[0]] > 0]
        ws_df = ws_df.sort_values(by=valid_ws_metrics[0], ascending=False)
        if len(valid_ws_metrics) == 1:
            fig_ws = px.bar(
                ws_df, x='Workstations', y=valid_ws_metrics[0], barmode='group',
                title='Operations per Workstation', color_discrete_sequence=chart_colors
            )
        else:
            fig_ws = px.bar(
                ws_df, x='Workstations', y=valid_ws_metrics, barmode='group',
                title='Operations per Workstation', color_discrete_sequence=chart_colors
            )
        fig_ws.update_traces(marker_line_width=0, marker_line_color="#333")
        fig_ws = style_chart(fig_ws)
        st.plotly_chart(fig_ws, use_container_width=True)
    else:
        st.info("No data available for the selected metrics in the current filters.")

    st.markdown("### ⚙️ Efficiency Score")
    st.caption("Efficiency = Total Refills / (Source Totes + Destination Totes). This gives a rough measure of how many refills are completed per tote moved.")
    filtered_df['Efficiency'] = filtered_df['TotalRefills'] / (filtered_df['SourceTotes'] + filtered_df['DestinationTotes'])
    eff_df = filtered_df.groupby('Username')['Efficiency'].mean().reset_index()
    eff_df = eff_df[eff_df['Efficiency'] > 0]
    eff_df = eff_df.sort_values(by='Efficiency', ascending=False)
    if not eff_df.empty:
        eff_df['Efficiency'] = eff_df['Efficiency'].round(0)
        fig_eff = px.bar(
            eff_df, x='Username', y='Efficiency', title='Average Efficiency per User',
            color_discrete_sequence=chart_colors, text='Efficiency'
        )
        fig_eff.update_traces(
            texttemplate='%{text:.0f}', 
            textposition='outside', 
            marker_line_width=0, 
            marker_line_color="#333", 
            textfont_size=16
        )
        fig_eff = style_chart(fig_eff)
        st.plotly_chart(fig_eff, use_container_width=True)
    else:
        st.info("No data available for the selected metrics in the current filters.")

    output = BytesIO()
    filtered_df.to_csv(output, index=False)
    st.download_button(
        "Download Filtered CSV", 
        data=output.getvalue(), 
        file_name="filtered_picking_data.csv", 
        mime="text/csv"
    )
else:
    st.info("Please upload a CSV file to begin.")


