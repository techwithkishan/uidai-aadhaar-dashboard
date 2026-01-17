import pandas as pd
import streamlit as st
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="UIDAI Aadhaar Enrollment Dashboard",
    layout="wide"
)

# ---------------- CSS FOR SUBTLE ANIMATIONS ----------------
st.markdown("""
<style>
[data-testid="stMetric"] {
    animation: fadeIn 1.2s ease-in;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("🇮🇳 UIDAI Aadhaar Enrollment Dashboard")
st.caption("Interactive analysis of state-wise, temporal, district-level and age-wise Aadhaar enrollments")

# ---------------- LOAD DATA ----------------
df = pd.read_csv("uidai_cleaned_datewise.csv")
df['date'] = pd.to_datetime(df['date'])

# ---------------- FEATURE ENGINEERING ----------------
df['total_enrollment'] = (
    df['age_0_5'] +
    df['age_5_17'] +
    df['age_18_greater']
)

df['month'] = df['date'].dt.month
df['month_name'] = df['date'].dt.strftime('%b')

# ---------------- INDIA MAP + KPIs ----------------
st.markdown("## 🌍 India-wide Overview")

state_summary = (
    df.groupby('clean_state', as_index=False)
      .agg({'total_enrollment': 'sum'})
)

col_map, col_kpi = st.columns([2.5, 1])

with col_map:
    fig_map = px.choropleth(
        state_summary,
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/india_states.geojson",
        featureidkey="properties.ST_NM",
        locations="clean_state",
        color="total_enrollment",
        color_continuous_scale="Reds",
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

with col_kpi:
    st.metric("Total Enrollments", f"{int(df['total_enrollment'].sum()):,}")
    st.metric("States / UTs Covered", df['clean_state'].nunique())
    st.metric("Total Records", f"{len(df):,}")

# ---------------- STATE SELECTION ----------------
st.markdown("---")
st.markdown("## 📍 State-wise Drill Down")

selected_state = st.selectbox(
    "Select State / Union Territory",
    sorted(df['clean_state'].unique())
)

state_df = df[df['clean_state'] == selected_state]

# ---------------- STATE KPIs ----------------
total_state = state_df['total_enrollment'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("📊 Total Enrollments (Year)", f"{int(total_state):,}")

# ---------------- MONTHLY TREND ----------------
monthly = (
    state_df
    .groupby(['month', 'month_name'], as_index=False)
    .agg({'total_enrollment': 'sum'})
    .sort_values('month')
)

fig_month = px.line(
    monthly,
    x='month_name',
    y='total_enrollment',
    markers=True,
    title=f"📈 Monthly Enrollment Trend – {selected_state}",
    line_shape="spline"
)

fig_month.update_traces(
    line=dict(width=4),
    marker=dict(size=8)
)

fig_month.update_layout(
    transition_duration=700,
    yaxis_title="Enrollments",
    xaxis_title="Month"
)

st.plotly_chart(fig_month, use_container_width=True)

# ---------------- PEAK / LOW MONTH ----------------
peak_month = monthly.loc[monthly['total_enrollment'].idxmax()]
low_month = monthly.loc[monthly['total_enrollment'].idxmin()]

colA, colB, colC = st.columns(3)
colA.metric("📈 Peak Month", peak_month['month_name'])
colB.metric("📉 Lowest Month", low_month['month_name'])

# ---------------- TOP DISTRICT ----------------
district_summary = (
    state_df
    .groupby('district', as_index=False)
    .agg({'total_enrollment': 'sum'})
    .sort_values('total_enrollment', ascending=False)
)

top_district = district_summary.iloc[0]
colC.metric("🏙️ Top District", top_district['district'])

# ---------------- AGE-WISE DISTRIBUTION ----------------
st.markdown("## 👶 Age-wise Enrollment Distribution")

age_data = pd.DataFrame({
    "Age Group": ["0–5", "5–17", "18+"],
    "Enrollments": [
        state_df['age_0_5'].sum(),
        state_df['age_5_17'].sum(),
        state_df['age_18_greater'].sum()
    ]
})

fig_age = px.bar(
    age_data,
    x="Age Group",
    y="Enrollments",
    color="Age Group",
    color_discrete_sequence=["#E63946", "#457B9D", "#2A9D8F"],
    title="Age-wise Enrollment Split"
)

fig_age.update_layout(
    yaxis_title="Enrollments",
    xaxis_title=""
)

st.plotly_chart(fig_age, use_container_width=True)

# ---------------- AGE-WISE PIE CHART ----------------
fig_age_pie = px.pie(
    age_data,
    names="Age Group",
    values="Enrollments",
    title="Age-wise Enrollment Share",
    hole=0.4,   # donut style (modern look)
    color="Age Group",
    color_discrete_sequence=["#E63946", "#457B9D", "#2A9D8F"]
)

fig_age_pie.update_traces(
    textposition='inside',
    textinfo='percent+label'
)

st.plotly_chart(fig_age_pie, use_container_width=True)


# ---------------- MONTH FILTER ----------------
st.markdown("## 🏘️ District-wise Analysis (Selected Month)")

month_map = monthly[['month', 'month_name']].drop_duplicates()

selected_month = st.selectbox(
    "Select Month",
    month_map.sort_values('month')['month_name']
)

month_df = state_df[state_df['month_name'] == selected_month]

district_month = (
    month_df
    .groupby('district', as_index=False)
    .agg({'total_enrollment': 'sum'})
    .sort_values('total_enrollment', ascending=False)
    .head(10)
)

fig_dist_month = px.bar(
    district_month,
    x='district',
    y='total_enrollment',
    title=f"Top Districts – {selected_state} ({selected_month})",
    hover_data={'total_enrollment': ':,'}
)

fig_dist_month.update_layout(
    yaxis_title="Enrollments",
    xaxis_title="District"
)

st.plotly_chart(fig_dist_month, use_container_width=True)

# ================= DOWNLOAD REPORTS =================
st.markdown("---")
st.markdown("## ⬇️ Download Reports")

# ---- FULL STATE DATA DOWNLOAD ----
state_csv = state_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Full State Data (CSV)",
    data=state_csv,
    file_name=f"{selected_state}_uidai_enrollment_data.csv",
    mime="text/csv"
)

# ---- YEARLY SUMMARY REPORT ----
summary_df = pd.DataFrame({
    "Metric": [
        "Total Enrollments",
        "Peak Month",
        "Lowest Month",
        "Top District",
        "Age 0–5 Enrollments",
        "Age 5–17 Enrollments",
        "Age 18+ Enrollments"
    ],
    "Value": [
        int(total_state),
        peak_month['month_name'],
        low_month['month_name'],
        top_district['district'],
        int(state_df['age_0_5'].sum()),
        int(state_df['age_5_17'].sum()),
        int(state_df['age_18_greater'].sum())
    ]
})

summary_csv = summary_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📄 Download State Yearly Summary (CSV)",
    data=summary_csv,
    file_name=f"{selected_state}_yearly_summary.csv",
    mime="text/csv"
)
