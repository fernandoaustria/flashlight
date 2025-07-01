import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Load preprocessed dataframe (must be in same folder as this script)
df = pd.read_csv('pivoted.csv', parse_dates=[
    'Submission Submitted At (Assignment Submissions1)_boy',
    'Submission Submitted At (Assignment Submissions1)_moy',
    'Submission Submitted At (Assignment Submissions1)_eoy'
])

# Sidebar filters
states = ['All'] + sorted(df['State Name (District School Students1)'].dropna().unique())
districts = ['All'] + sorted(df['District Name (District School Students1)'].dropna().unique())
grades = ['All'] + sorted(df['grade_num'].dropna().unique())

st.title("Benchmark Growth Dashboard")

st.sidebar.header("Filter")
selected_state = st.sidebar.selectbox("State", options=states)
selected_district = st.sidebar.selectbox("District", options=districts)
selected_grade = st.sidebar.selectbox("Grade", options=grades)

filtered = df.copy()
if selected_state != 'All':
    filtered = filtered[filtered['State Name (District School Students1)'] == selected_state]
if selected_district != 'All':
    filtered = filtered[filtered['District Name (District School Students1)'] == selected_district]
if selected_grade != 'All':
    filtered = filtered[filtered['grade_num'] == float(selected_grade)]

if filtered.empty:
    st.warning("No data available for this selection.")
    st.stop()

# Mean SpeakAverage Trend
st.markdown("### Mean SpeakAverage Trend")
fig, ax = plt.subplots()
ax.plot(['BOY', 'MOY', 'EOY'],
        [
            filtered["SpeakAverage_boy"].mean(),
            filtered["SpeakAverage_moy"].mean(),
            filtered["SpeakAverage_eoy"].mean()
        ],
        marker='o'
)
ax.set_ylabel("Mean SpeakAverage")
ax.set_xlabel("Benchmark")
st.pyplot(fig)

# Mean WriteAverage Trend
st.markdown("### Mean WriteAverage Trend")
fig, ax = plt.subplots()
ax.plot(['BOY', 'MOY', 'EOY'],
        [
            filtered["WriteAverage_boy"].mean(),
            filtered["WriteAverage_moy"].mean(),
            filtered["WriteAverage_eoy"].mean()
        ],
        marker='o'
)
ax.set_ylabel("Mean WriteAverage")
ax.set_xlabel("Benchmark")
st.pyplot(fig)

st.markdown("### Days Between Benchmarks - Summary")
for col in ['days_boy_moy', 'days_moy_eoy', 'days_boy_eoy']:
    days = filtered[col].dropna()
    st.write(
        f"**{col.replace('_', ' ').upper()}:** "
        f"Mean = {days.mean():.1f} days, "
        f"SD = {days.std():.1f} days, "
        f"N = {days.count()}"
    )

st.markdown(f"### Students: {len(filtered)}")

# Show aggregate statistics
st.markdown("#### Growth Statistics")
growth_cols = [
    'SpeakAverage_growth_BOY_MOY', 'SpeakAverage_growth_MOY_EOY', 'SpeakAverage_growth_BOY_EOY',
    'WriteAverage_growth_BOY_MOY', 'WriteAverage_growth_MOY_EOY', 'WriteAverage_growth_BOY_EOY'
]
st.dataframe(filtered[growth_cols].describe().T[['mean', 'std', 'min', 'max', 'count']])

# Mean growth by grade
st.markdown("#### Mean Growth by Grade")
st.dataframe(
    filtered.groupby('grade_num')[growth_cols].mean().reset_index()
)

# Histogram of days between BOY-MOY
st.markdown("#### Days Between Benchmarks (BOY-MOY)")
st.bar_chart(filtered['days_boy_moy'].dropna())

# Student-level Data
st.markdown("#### Student-level Data (first 100 rows)")
st.dataframe(filtered.head(100))
