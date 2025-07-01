#Load preprocessed dataframe

# Load the preprocessed data
df = pd.read_csv('pivoted.csv', parse_dates=[
    'Submission Submitted At (Assignment Submissions1)_boy',
    'Submission Submitted At (Assignment Submissions1)_moy',
    'Submission Submitted At (Assignment Submissions1)_eoy'
])

# Sidebar filters
states = ['All'] + sorted(df['State Name (District School Students1)'].dropna().unique())
districts = ['All'] + sorted(df['District Name (District School Students1)'].dropna().unique())
grades = ['All'] + sorted(df['grade_num'].dropna().unique())

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
    
st.markdown("### Days Between Benchmarks - Summary")
for col in ['days_boy_moy', 'days_moy_eoy', 'days_boy_eoy']:
    days = filtered[col].dropna()
    st.write(
        f"**{col.replace('_', ' ').upper()}:** "
        f"Mean = {days.mean():.1f} days, "
        f"SD = {days.std():.1f} days, "
        f"N = {days.count()}"
    )

st.title("Benchmark Growth Dashboard")

st.markdown(f"### Students: {len(filtered)}")

# Show aggregate statistics
st.markdown("#### Growth Statistics")
growth_cols = [
    'SpeakAverage_growth_BOY_MOY', 'SpeakAverage_growth_MOY_EOY', 'SpeakAverage_growth_BOY_EOY',
    'WriteAverage_growth_BOY_MOY', 'WriteAverage_growth_MOY_EOY', 'WriteAverage_growth_BOY_EOY'
]
st.dataframe(filtered[growth_cols].describe().T[['mean', 'std', 'min', 'max', 'count']])

# Example: Mean growth by grade
st.markdown("#### Mean Growth by Grade")
st.dataframe(
    filtered.groupby('grade_num')[growth_cols].mean().reset_index()
)

# Plot example: Histogram of days between BOY-MOY
st.markdown("#### Days Between Benchmarks (BOY-MOY)")
st.bar_chart(filtered['days_boy_moy'].dropna())

# Drill down to student table
st.markdown("#### Student-level Data (first 100 rows)")
st.dataframe(filtered.head(100))

# Optionally: Add more visualizations!
