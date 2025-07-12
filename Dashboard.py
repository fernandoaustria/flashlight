import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import re

df = pd.read_csv('pivoted.csv', parse_dates=[
    'Submission Submitted At (Assignment Submissions1)_boy',
    'Submission Submitted At (Assignment Submissions1)_moy',
    'Submission Submitted At (Assignment Submissions1)_eoy'
])

states = ['All'] + sorted(df['State Name (District School Students1)'].dropna().unique())
districts = ['All'] + sorted(df['District Name (District School Students1)'].dropna().unique())
schools = ['All'] + sorted(df['School Name (District School Students1)'].dropna().unique())
grade_bands = ['All'] + sorted(df['grade_band'].dropna().astype(str).unique())
grades = ['All'] + sorted(df['grade_num'].dropna().unique())

st.title("Benchmark Growth Dashboard")
st.sidebar.header("Filter")
selected_state = st.sidebar.selectbox("State", options=states)
selected_district = st.sidebar.selectbox("District", options=districts)
selected_school = st.sidebar.selectbox("School", options=schools)
selected_grade_band = st.sidebar.selectbox("Grade Band", options=grade_bands)
selected_grade = st.sidebar.selectbox("Grade", options=grades)

filtered = df.copy()
if selected_state != 'All':
    filtered = filtered[filtered['State Name (District School Students1)'] == selected_state]
if selected_district != 'All':
    filtered = filtered[filtered['District Name (District School Students1)'] == selected_district]
if selected_school != 'All':
    filtered = filtered[filtered['School Name (District School Students1)'] == selected_school]
if selected_grade_band != 'All':
    filtered = filtered[filtered['grade_band'].astype(str) == selected_grade_band]
if selected_grade != 'All':
    filtered = filtered[filtered['grade_num'] == float(selected_grade)]

if filtered.empty:
    st.warning("No data available for this selection.")
    st.stop()

#All1s tables

# All1s Table
def parse_flags(flag):
    if pd.isna(flag):
        return []
    # Lowercase, replace commas/newlines with space, split on whitespace
    return [x.strip().upper() for x in re.split(r'[,;\s]+', str(flag)) if x.strip()]

def count_non_la(flag):
    codes = parse_flags(flag)
    return any(code != 'LA' for code in codes if code)  # True if any flag is NOT LA

def count_code(flag, code):
    codes = parse_flags(flag)
    return codes.count(code)
    
def all1s_summary_v2(df, benchmark='boy', group_col='School Name (District School Students1)'):
    col = f'All1s_{benchmark}'
    group = df[[group_col, col]].copy()
    group[col] = group[col].fillna('')

    summary = group.groupby(group_col).agg(
        N=(col, 'size'),
        Non_LA_All1s=(col, lambda x: x.apply(count_non_la).sum()),
        TI=(col, lambda x: x.apply(lambda v: count_code(v, 'TI')).sum()),
        SS=(col, lambda x: x.apply(lambda v: count_code(v, 'SS')).sum()),
        OT=(col, lambda x: x.apply(lambda v: count_code(v, 'OT')).sum()),
        NT=(col, lambda x: x.apply(lambda v: count_code(v, 'NT')).sum()),
        LA=(col, lambda x: x.apply(lambda v: count_code(v, 'LA')).sum())
    ).reset_index()
    summary['%'] = (summary['Non_LA_All1s'] / summary['N'] * 100).round(1).astype(str) + '%'
    return summary

#Display tables
st.markdown("### All1s Flags Summary by School")
for bench in ['boy', 'moy', 'eoy']:
    st.markdown(f"#### {bench.upper()} All1s by School")
    table = all1s_summary_v2(filtered, benchmark=bench, group_col='School Name (District School Students1)')
    st.dataframe(table)
    csv = table.to_csv(index=False)
    st.download_button(
        label=f"Download {bench.upper()} All1s Summary (CSV)",
        data=csv,
        file_name=f"{bench}_all1s_summary.csv",
        mime="text/csv"
    )



# Interactive Trend Plot
score_option = st.selectbox(
    "Select Score for Trend",
    options=["SpeakAverage", "WriteAverage"],
    index=0
)

means = [
    filtered.get(f"{score_option}_boy", pd.Series(dtype='float')).mean(),
    filtered.get(f"{score_option}_moy", pd.Series(dtype='float')).mean(),
    filtered.get(f"{score_option}_eoy", pd.Series(dtype='float')).mean()
]
benchmarks = ["BOY", "MOY", "EOY"]

st.markdown(f"### Mean {score_option} Trend")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=benchmarks, y=means,
    mode='lines+markers',
    name=f"Mean {score_option}"
))
fig.update_layout(
    xaxis_title="Benchmark",
    yaxis_title=f"Mean {score_option}",
    hovermode='x unified'
)
st.plotly_chart(fig, use_container_width=True)

# By Grade
means_by_grade = (
    filtered.groupby('grade_num')[
        [f"{score_option}_boy", f"{score_option}_moy", f"{score_option}_eoy"]
    ]
    .mean()
    .reset_index()
)

means_by_grade_melted = means_by_grade.melt(
    id_vars='grade_num',
    value_vars=[f"{score_option}_boy", f"{score_option}_moy", f"{score_option}_eoy"],
    var_name='benchmark',
    value_name='mean_score'
)
means_by_grade_melted['benchmark'] = means_by_grade_melted['benchmark'].str.extract(f"{score_option}_(.*)").iloc[:, 0].str.upper()

st.markdown(f"### {score_option} Trend by Grade")
fig = go.Figure()
for grade, group in means_by_grade_melted.groupby('grade_num'):
    fig.add_trace(go.Scatter(
        x=group['benchmark'], y=group['mean_score'],
        mode='lines+markers',
        name=f'Grade {grade}'
    ))
fig.update_layout(
    xaxis_title="Benchmark",
    yaxis_title=f"Mean {score_option}",
    legend_title="Grade",
    hovermode='x unified'
)
st.plotly_chart(fig, use_container_width=True)

# Days between benchmarks summary
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

# Growth stats
st.markdown("#### Growth Statistics")
growth_cols = [
    'SpeakAverage_growth_BOY_MOY', 'SpeakAverage_growth_MOY_EOY', 'SpeakAverage_growth_BOY_EOY',
    'WriteAverage_growth_BOY_MOY', 'WriteAverage_growth_MOY_EOY', 'WriteAverage_growth_BOY_EOY'
]
st.dataframe(filtered[growth_cols].describe().T[['mean', 'std', 'min', 'max', 'count']])

# Growth by grade
st.markdown("#### Mean Growth by Grade")
st.dataframe(
    filtered.groupby('grade_num')[growth_cols].mean().reset_index()
)

