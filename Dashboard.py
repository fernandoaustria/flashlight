import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import re

df = pd.read_csv(
    'pivoted.csv',
    parse_dates=[
        'Submission Submitted At (Assignment Submissions1)_boy',
        'Submission Submitted At (Assignment Submissions1)_moy',
        'Submission Submitted At (Assignment Submissions1)_eoy'
    ],
    low_memory=False
)

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
    # Create the percentage column
    summary['%'] = (summary['Non_LA_All1s'] / summary['N'] * 100).round(1).astype(str) + '%'
    # Move '%' column to be right after 'Non_LA_All1s'
    cols = list(summary.columns)
    percent_col = cols.pop(cols.index('%'))
    cols.insert(cols.index('Non_LA_All1s') + 1, percent_col)
    summary = summary[cols]
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

#Participation in Benchmark
def benchmark_participation_summary(df, group_col='School Name (District School Students1)'):
    result = df.groupby(group_col).agg(
        N=('Student Number (District School Students1)', 'count'),
        BOY=('SpeakAverage_boy', lambda x: x.notna().sum()),
        MOY=('SpeakAverage_moy', lambda x: x.notna().sum()),
        EOY=('SpeakAverage_eoy', lambda x: x.notna().sum())
    ).reset_index()
    result['% BOY'] = (result['BOY'] / result['N'] * 100).round(1).astype(str) + '%'
    result['% MOY'] = (result['MOY'] / result['N'] * 100).round(1).astype(str) + '%'
    result['% EOY'] = (result['EOY'] / result['N'] * 100).round(1).astype(str) + '%'
    return result

# Example: By School
st.markdown("### Student Participation by School")
summary_table = benchmark_participation_summary(filtered)
st.dataframe(summary_table)
csv = summary_table.to_csv(index=False)
st.download_button("Download Participation Table (CSV)", data=csv, file_name="participation_by_school.csv")

# Interactive Trend Plot
score_option = st.selectbox(
    "Select Score for Trend",
    options=["SpeakAverage", "WriteAverage"],
    index=0
)

for bench in ['boy', 'moy', 'eoy']:
    col = f'All1s_{bench}'
    filtered[f'no_flag_{bench}'] = filtered[col].isna() | (filtered[col].astype(str).str.strip() == '')

means = [
    filtered.loc[filtered['no_flag_boy'], f"{score_option}_boy"].mean(),
    filtered.loc[filtered['no_flag_moy'], f"{score_option}_moy"].mean(),
    filtered.loc[filtered['no_flag_eoy'], f"{score_option}_eoy"].mean()
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
means_boy = filtered.loc[filtered['no_flag_boy']].groupby('grade_num')[f"{score_option}_boy"].mean()
means_moy = filtered.loc[filtered['no_flag_moy']].groupby('grade_num')[f"{score_option}_moy"].mean()
means_eoy = filtered.loc[filtered['no_flag_eoy']].groupby('grade_num')[f"{score_option}_eoy"].mean()

means_by_grade = pd.DataFrame({
    'grade_num': sorted(set(means_boy.index) | set(means_moy.index) | set(means_eoy.index)),
})
means_by_grade = means_by_grade.set_index('grade_num')
means_by_grade[f"{score_option}_boy"] = means_boy
means_by_grade[f"{score_option}_moy"] = means_moy
means_by_grade[f"{score_option}_eoy"] = means_eoy
means_by_grade = means_by_grade.reset_index()
    
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
for (a, b) in [('boy', 'moy'), ('moy', 'eoy'), ('boy', 'eoy')]:
    mask = filtered[f'no_flag_{a}'] & filtered[f'no_flag_{b}']
    col = f'days_{a}_{b}'
    days = filtered.loc[mask, col].dropna()
    st.write(
        f"**{col.replace('_', ' ').upper()}:** "
        f"Mean = {days.mean():.1f} days, "
        f"SD = {days.std():.1f} days, "
        f"N = {days.count()}"
    )

#Create filter mask
n_no_flag_all = filtered['no_flag_boy'] & filtered['no_flag_moy'] & filtered['no_flag_eoy']
st.markdown(f"### Students with no flags in any window: {n_no_flag_all.sum()}")

# Growth stats
growth_cols = [
    'SpeakAverage_growth_BOY_MOY', 'SpeakAverage_growth_MOY_EOY', 'SpeakAverage_growth_BOY_EOY',
    'WriteAverage_growth_BOY_MOY', 'WriteAverage_growth_MOY_EOY', 'WriteAverage_growth_BOY_EOY'
]

st.markdown("#### Growth Statistics")
growth_stats = {}
for skill in ['SpeakAverage', 'WriteAverage']:
    for pair in [('BOY', 'MOY'), ('MOY', 'EOY'), ('BOY', 'EOY')]:
        a, b = pair[0].lower(), pair[1].lower()
        col = f'{skill}_growth_{pair[0]}_{pair[1]}'
        mask = filtered[f'no_flag_{a}'] & filtered[f'no_flag_{b}']
        vals = filtered.loc[mask, col].dropna()
        growth_stats[col] = [vals.mean(), vals.std(), vals.min(), vals.max(), vals.count()]
stats = pd.DataFrame(
    growth_stats, index=['mean', 'std', 'min', 'max', 'count']
).T.round(2)
st.dataframe(stats)

# Growth by grade (filtered for flags)
st.markdown("#### Mean Growth by Grade")
by_grade = pd.DataFrame({'grade_num': sorted(filtered['grade_num'].dropna().unique())}).set_index('grade_num')
for skill in ['SpeakAverage', 'WriteAverage']:
    for pair in [('BOY', 'MOY'), ('MOY', 'EOY'), ('BOY', 'EOY')]:
        a, b = pair[0].lower(), pair[1].lower()
        col = f'{skill}_growth_{pair[0]}_{pair[1]}'
        mask = filtered[f'no_flag_{a}'] & filtered[f'no_flag_{b}']
        means = filtered.loc[mask].groupby('grade_num')[col].mean()
        by_grade[col] = means
by_grade = by_grade.round(2).reset_index()
st.dataframe(by_grade)

# Growth by grade band (filtered for flags)
st.markdown("#### Mean Growth by Grade Band")
by_band = pd.DataFrame({'grade_band': sorted(filtered['grade_band'].dropna().astype(str).unique())}).set_index('grade_band')
for skill in ['SpeakAverage', 'WriteAverage']:
    for pair in [('BOY', 'MOY'), ('MOY', 'EOY'), ('BOY', 'EOY')]:
        a, b = pair[0].lower(), pair[1].lower()
        col = f'{skill}_growth_{pair[0]}_{pair[1]}'
        mask = filtered[f'no_flag_{a}'] & filtered[f'no_flag_{b}']
        means = filtered.loc[mask].groupby('grade_band')[col].mean()
        by_band[col] = means
by_band = by_band.round(2).reset_index()
st.dataframe(by_band)

# NLP features selector
# ---- NLP Feature Multi-Selector ----
st.sidebar.header("NLP / Feature Explorer")

nlp_prefixes = [
    "n_tokens", "avg_token_sent", "flesch_reading_ease", "fk_grade", "grammar_errors",
    "n_sents", "pct_noun", "pct_verb", "ttr"
]
nlp_cols = [col for col in filtered.columns if any(col.startswith(prefix) for prefix in nlp_prefixes)]

selected_features = st.sidebar.multiselect(
    "Select NLP feature(s) to visualize", 
    sorted(nlp_cols),
    default=[nlp_cols[0]] if nlp_cols else []
)

flag_filter = st.sidebar.checkbox("Only students with NO All1s flag in any window", value=False)
if flag_filter:
    n_no_flag_all = filtered['no_flag_boy'] & filtered['no_flag_moy'] & filtered['no_flag_eoy']
    filtered_plot = filtered.loc[n_no_flag_all]
else:
    filtered_plot = filtered

if selected_features:
    # Side-by-side Histograms
    st.markdown("### Histograms for Selected Features")
    n_features = len(selected_features)
    fig, axs = plt.subplots(1, n_features, figsize=(5 * n_features, 4))
    if n_features == 1:
        axs = [axs]
    for ax, selected_feature in zip(axs, selected_features):
        feature_data = filtered_plot[selected_feature].dropna()
        ax.hist(feature_data, bins='auto')
        ax.set_xlabel(selected_feature)
        ax.set_ylabel("Frequency")
        ax.set_title(selected_feature)
    st.pyplot(fig)
    plt.close(fig)

    # Side-by-side Boxplots by grade_num
    if 'grade_num' in filtered_plot.columns:
        st.markdown("### Boxplots by Grade for Selected Features")
        fig, axs = plt.subplots(1, n_features, figsize=(5 * n_features, 4))
        if n_features == 1:
            axs = [axs]
        for ax, selected_feature in zip(axs, selected_features):
            sns.boxplot(
                x=filtered_plot['grade_num'],
                y=filtered_plot[selected_feature],
                ax=ax
            )
            ax.set_xlabel("Grade")
            ax.set_ylabel(selected_feature)
            ax.set_title(selected_feature)
        st.pyplot(fig)
        plt.close(fig)

    # Side-by-side Boxplots by grade_band
    if 'grade_band' in filtered_plot.columns:
        st.markdown("### Boxplots by Grade Band for Selected Features")
        fig, axs = plt.subplots(1, n_features, figsize=(5 * n_features, 4))
        if n_features == 1:
            axs = [axs]
        for ax, selected_feature in zip(axs, selected_features):
            sns.boxplot(
                x=filtered_plot['grade_band'],
                y=filtered_plot[selected_feature],
                ax=ax
            )
            ax.set_xlabel("Grade Band")
            ax.set_ylabel(selected_feature)
            ax.set_title(selected_feature)
            ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)
        plt.close(fig)
if selected_features:
    # ... your plots here ...
    st.markdown("### Summary Table for Selected Features")
    summary_df = filtered_plot[selected_features].describe().T
    st.dataframe(summary_df)

    st.markdown("### Data Preview for Selected Features")
    st.dataframe(filtered_plot[selected_features].head(30))

    csv = filtered_plot[selected_features].to_csv(index=False)
    st.download_button(
        label="Download selected features (CSV)",
        data=csv,
        file_name="selected_nlp_features.csv",
        mime="text/csv"
    )
