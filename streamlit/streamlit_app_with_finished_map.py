import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data as vega_data


# Page configuration
st.set_page_config(
    page_title="Cancer Risk Factors Across the US",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Risk factors organized by category
RISK_FACTORS = {
    "Environmental": [
        "Occupational risks",
        "Unsafe water, sanitation, and handwashing",
        "Air pollution",
        "Non-optimal temperature",
        "Other environmental risks"
    ],
    "Behavioral": [
        "Tobacco",
        "High alcohol use",
        "Drug use",
        "Dietary risks",
        "Unsafe sex",
        "Low physical activity",
        "Intimate partner violence",
        "Sexual violence against children and bullying",
        "Child and maternal malnutrition"
    ],
    "Metabolic": [
        "High fasting plasma glucose",
        "High LDL cholesterol",
        "High systolic blood pressure",
        "High body-mass index",
        "Low bone mineral density",
        "Kidney dysfunction"
    ]
}

# Flatten risk factors for easy access
ALL_RISK_FACTORS = []
for category, factors in RISK_FACTORS.items():
    ALL_RISK_FACTORS.extend(factors)

# Available years
AVAILABLE_YEARS = [1990, 1995, 2000, 2005, 2010, 2015, 2020]

@st.cache_data
def load_data():
    # Load deaths and risks data
    deaths_df = pd.read_csv("data/Deaths.csv", low_memory=False)
    risks_df = pd.read_csv("data/RateDALY.csv", low_memory=False)
    
    # Load state codes and merge with risks data
    state_codes = pd.read_csv("data/stateCodes.csv")
    risks_df = risks_df.merge(state_codes, left_on="location_name", right_on="state", how="left")
    risks_df = risks_df[risks_df['rei_name'] != 'rei_name']
    risks_df['year'] = pd.to_numeric(risks_df['year'], errors='coerce').astype(int)
    
    risks_df['val'] = pd.to_numeric(risks_df['val'], errors='coerce')

    return deaths_df, risks_df


def get_default_cancer(risks_df):
    # Get a default cancer type (second in sorted list)
    cancers = sorted(risks_df['cause_name'].unique())
    #st. write("Available cancers for default selection:", cancers)

    return cancers[1] if len(cancers) > 0 else None

def get_filtered_data(risks_df, selected_risks, year=None, year_range=None):
    # Filter risks_df based on selected risks and time
    filtered = risks_df[risks_df['rei_name'].isin(selected_risks)]

    if year is not None:
        filtered = filtered[filtered['year'] == year]
    elif year_range is not None:
        filtered = filtered[(filtered['year'] >= year_range[0]) & 
                          (filtered['year'] <= year_range[1])]
    return filtered

def get_cancer_list(risks_df):
    # Get unique list of cancer types from data
    return sorted(risks_df['cause_name'].unique())

def get_state_list(risks_df):
    # Get unique list of states from data
    return sorted(risks_df['location_name'].unique())

# Initialize session state for selected cancer
if 'selected_cancer' not in st.session_state:
    st.session_state.selected_cancer = None
    st.session_state.needs_default = True 

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Main Dashboard", "About"])

if page == "About":
    st.title("About This Project")
    st.markdown("""
    ## Cancer Risk Factors Analysis
    
    ### Project Description
    
    This interactive dashboard explores how different risk factors contribute to various cancer types 
    across the United States over time. 
    
    **Data Source:**

    > Global Burden of Disease Collaborative Network.
    > 
    > Global Burden of Disease Study 2023 (GBD 2023) Results.
    >
    > Seattle, United States: Institute for Health Metrics and Evaluation (IHME), 2024.
    >
    > Available from https://vizhub.healthdata.org/gbd-results/.
    
    **Risk Factor Categories:**
    
    **Environmental Factors:**
    - Occupational risks
    - Water and sanitation quality
    - Air pollution
    - Temperature extremes
    - Other environmental hazards
    
    **Behavioral Factors:**
    - Tobacco use
    - Alcohol consumption
    - Drug use
    - Dietary patterns
    - Physical activity levels
    - Sexual behaviors
    - Violence exposure
    - Maternal and child nutrition
    
    **Metabolic Factors:**
    - Blood glucose levels
    - Cholesterol levels
    - Blood pressure
    - Body mass index
    - Bone density
    - Kidney function
    
    **How to Use This Dashboard:**
    1. Select risk factors you want to analyze
    2. Choose a specific year or time range
    3. Explore the heatmap to see risk-cancer relationships
    4. Click a heatmap cell to view detailed cancer-specific state and temporal analyses
    
    **Team Members:**
    Sriya, Jack, Zoe, and Ryan
    
    **Last Updated:** December 2025
    """)

else:
    # Main Dashboard
    st.title("📊 Cancer Risk Factors Across the US")
    st.markdown("Explore how environmental, behavioral, and metabolic risk factors contribute to different cancer types across states and time")
    
    # Load data
    try:
        deaths_df, risks_df = load_data()
        st.sidebar.success("✓ Data loaded successfully")
        
        # Set default cancer if needed
        if st.session_state.needs_default or st.session_state.selected_cancer is None:
            st.session_state.selected_cancer = get_default_cancer(risks_df)
            st.session_state.needs_default = False
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure Deaths.csv and Risks.csv are in the data/ folder")
        st.stop()
    
    st.sidebar.header("Filters")
    
    # Risk factor selection
    st.sidebar.subheader("1. Select Risk Factors")
    
    # Quick selection buttons 
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        if    st.button("All Environmental", use_container_width=True):
            st.session_state.selected_risks = RISK_FACTORS["Environmental"].copy()
    
    with col2:
        if st.button("All Behavioral", use_container_width=True):
            st.session_state.selected_risks = RISK_FACTORS["Behavioral"].copy()
    
    with col3:
        if st.button("All Metabolic", use_container_width=True):
            st.session_state.selected_risks = RISK_FACTORS["Metabolic"].copy()
    
    # Initialize selected_risks 
    if 'selected_risks' not in st.session_state:
        st.session_state.selected_risks = ["Tobacco", "High alcohol use", "Air pollution"]
    
    # Multi-select with grouping
    selected_risks = st.sidebar.multiselect(
        "Choose risk factors to analyze:",
        options=ALL_RISK_FACTORS,
        default=st.session_state.selected_risks,
        help="Select one or more risk factors. Use the buttons above to quickly select all factors in a category."
    )
    
    # Update session state
    st.session_state.selected_risks = selected_risks
    # Show selected categories
    if selected_risks:
        selected_categories = []
        for category, factors in RISK_FACTORS.items():
            if any(risk in selected_risks for risk in factors):
                selected_categories.append(category)
        st.sidebar.caption(f"Categories: {', '.join(selected_categories)}")
    
    # Time period selection
    st.sidebar.subheader("2. Select Time Period")
    
    # Toggle between single year and range
    time_mode = st.sidebar.radio(
        "Selection mode:",
        options=["Single Year", "Year Range"],
        horizontal=True
    )
    
    if time_mode == "Single Year":
        selected_year = st.sidebar.select_slider(
            "Select year:",
            options=AVAILABLE_YEARS,
            value=2010
        )
        year_range = None
        time_display = f"Year: {selected_year}"
    else:
        year_range = st.sidebar.select_slider(
            "Select year range:",
            options=AVAILABLE_YEARS,
            value=(1995, 2015)
        )
        selected_year = None
        time_display = f"Years: {year_range[0]} - {year_range[1]}"
    
    st.sidebar.caption(time_display)
    
    # === MAIN CONTENT AREA ===
    
    # Show current selections
    st.info(f"**Analyzing {len(selected_risks)} risk factor(s)** | **{time_display}**")
    
    if not selected_risks:
        st.warning("⚠️ Please select at least one risk factor to begin analysis")
        st.stop()
    
    # === VISUALIZATION 1: HEATMAP ===
    st.header("Cancer Types vs Risk Factors")
    st.markdown("**Click on a cancer type** to update the geographic and temporal visualizations below")
    
    filtered_data = get_filtered_data(
            risks_df, 
            selected_risks, 
            year=selected_year, 
            year_range=year_range
        )
    
    cancer_selector = alt.selection_point(
        fields=["cause_name"],
        name="cancerSelect",
        on="click",
        empty="none",
        clear=False
    )

    # Heatmap Code
    heatmap = (
        alt.Chart(filtered_data)
        .mark_rect()
        .encode(
            x = alt.X('rei_name', title = 'Risk Factors'),
            y = alt.Y('cause_name', title='Cancer Type'),
            color=alt.Color(
                'val',
                title="Risk Contribution",
                scale=alt.Scale(scheme="blueorange", domainMid=10)
            ),
            stroke=alt.condition(cancer_selector, alt.value("grey"), alt.value(None)),
            strokeWidth=alt.condition(cancer_selector, alt.value(2), alt.value(0)),
            tooltip=[alt.Tooltip('cause_name:N', title='Cancer Type'), alt.Tooltip('rei_name:N', title='Risk Factor'), alt.Tooltip('val:Q', title='Risk Contribution', format=".2f")],
            opacity=alt.condition(cancer_selector, alt.value(1), alt.value(0.30))
        ).add_params(cancer_selector)
    )

    event = st.altair_chart(heatmap, key="heatmap", on_select="rerun")
    
    selected_val = None
    if event:
        sel = event.get("selection", {})
        cancer_sel = sel.get("cancerSelect", [])

        if isinstance(cancer_sel, list) and len(cancer_sel) > 0:
            selected_val = cancer_sel[0].get("cause_name")

    if selected_val:
        st.session_state.selected_cancer = selected_val

    st.markdown("---")
    # === VISUALIZATIONS 2 & 3 ===

    # Detailed analysis for selected cancer
    st.markdown("### Detailed Analysis")
    st.info(f"**Cancer: {st.session_state.selected_cancer}**")
    st.caption("Click a different cancer in the heatmap above to update these visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Geographic Distribution")
        st.caption(f"Risk factors for {st.session_state.selected_cancer} across US states, calculated by DALYs are Disability-Adjusted Life Years, a measure of overall disease burden.")
        
        # Filter Data
        filtered_data = get_filtered_data(
            risks_df, 
            selected_risks, 
            year=selected_year, 
            year_range=year_range
        )
                
        # Filter for selected cancer and aggregate by state
        # Count how many data points each state has
        state_counts = filtered_data[
            (filtered_data['cause_name'] == st.session_state.selected_cancer)
        ].groupby(['location_name', 'mapid']).size().reset_index(name='count')

        # Sum the values
        state_sums = filtered_data[
            (filtered_data['cause_name'] == st.session_state.selected_cancer)
        ].groupby(['location_name', 'mapid']).agg({
            'val': 'sum'
        }).reset_index()

        # Merge and calculate avg
        deaths_ss = state_sums.merge(state_counts, on=['location_name', 'mapid'])
        deaths_ss['val'] = deaths_ss['val'] / deaths_ss['count']

        # Check if we have any data
        if deaths_ss.empty or len(deaths_ss) == 0:
            st.warning(f"⚠️ No data available for **{st.session_state.selected_cancer}** with the selected risk factors and time period.")
            st.info("Try selecting different risk factors, a different time period, or a different cancer type.")
        else:
            # Clean the data
            deaths_ss = deaths_ss.dropna(subset=['mapid', 'val'])
            deaths_ss['mapid'] = deaths_ss['mapid'].astype(int)

            # Load states geojson for the map 
            states = alt.topo_feature(vega_data.us_10m.url, feature='states')
            try:
                # Create the map visualization
                states_map = alt.Chart(states).mark_geoshape().encode(
                    color=alt.Color('val:Q', title='Avg. DALYs Rate (per 100k)', scale=alt.Scale(domainMid=10, scheme='blueorange')), 
                    tooltip=[alt.Tooltip('location_name:N', title='State'), alt.Tooltip('val:Q', title='Avg. DALYs Rate (per 100k)', format=".2f")]
                ).transform_lookup(
                    lookup='id',
                    from_=alt.LookupData(deaths_ss, 'mapid', list(deaths_ss.columns))
                ).properties(
                    width=500,
                    height=300
                ).project(
                    type='albersUsa'
                )
                
                st.altair_chart(states_map, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render map: {e}")
                st.info("Map visualization requires proper geographic data structure.")
    


    def render_lineplot(
        risks_df: pd.DataFrame,
        selected_risks,
        selected_cancer: str,
        selected_year: int | None,
        year_range: tuple[int, int] | None,
        time_display: str,
    ):
        """
        Render an Altair line plot of risk factor trends over time.

        Parameters
        ----------
        risks_df : pd.DataFrame
            Full risks dataframe (already loaded in streamlit_app.py).
        selected_risks : list[str]
            Risk factor names selected in the sidebar.
        selected_cancer : str
            Currently selected cancer type (from session_state).
        selected_year : int or None
            Single year if time mode is 'Single Year'.
        year_range : (int, int) or None
            (start_year, end_year) if time mode is 'Year Range'.
        time_display : str
            Human-readable time label (e.g. "Year: 2010" or "Years: 1995 - 2015").
        """
        df = risks_df.copy()

        if "measure_name" in df.columns:
            df = df[df["measure_name"] != "Deaths"]

        # Filter by selected cancer type
        df = df[df["cause_name"] == selected_cancer]

        # Filter by selected risk factors
        df = df[df["rei_name"].isin(selected_risks)]

        df["year"] = df["year"].astype(int)
        df["val"] = df["val"].astype(float)

        # Filter by time
        if selected_year is not None:
            df = df[df["year"] == selected_year]
        elif year_range is not None:
            df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]
        

        if df.empty:
            st.warning(
                "No data available for this cancer, risk factors, and time selection. "
                "Try changing the filters in the sidebar."
            )
            return

        # Aggregate across locations / sex / age: mean val per (year, risk factor)
        agg_df = (
            df.groupby(["year", "rei_name"], as_index=False)["val"]
            .mean()
        )

        # Build the line chart
        chart = (
            alt.Chart(agg_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("year:O", title="Year"),
                y=alt.Y("val:Q", title="Avg. DALYs Rate (per 100k)"),
                color=alt.Color("rei_name:N", title="Risk factor"),
                tooltip=[
                    alt.Tooltip("year:O", title="Year"),
                    alt.Tooltip("rei_name:N", title="Risk factor"),
                    alt.Tooltip("val:Q", title="Avg. DALYs Rate (per 100k)", format=".2f"),
                ],
            )
            .properties(
                height=350,
                title=f"Temporal trends for {selected_cancer}\n{time_display}",
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)


    with col2:
        st.subheader("Temporal Distribution")
        st.caption(f"Risk factor trends over time for {st.session_state.selected_cancer}")


        #####  This needs to be removed once the heatmap is ready
        def get_cancer_list(risks_df):
            """Get unique list of cancer types from data"""
            return sorted(risks_df['cause_name'].unique())
        
        cancer_list = get_cancer_list(risks_df)
        if (
            "selected_cancer" not in st.session_state
            or st.session_state.selected_cancer not in cancer_list
        ):
            st.session_state.selected_cancer = get_default_cancer(risks_df)

   
        render_lineplot(
            risks_df=risks_df,
            selected_risks=selected_risks,
            selected_cancer=st.session_state.selected_cancer,
            selected_year=selected_year,
            year_range=year_range,
            time_display=time_display,
        )

        
    
    # === ADDITIONAL INFO ===
    with st.expander("ℹ️ Data Information"):
        st.write(f"**Total rows in Deaths data:** {len(deaths_df):,}")
        st.write(f"**Total rows in Risks data:** {len(risks_df):,}")
        st.write(f"**Available risk factors in data:** {len(risks_df['rei_name'].unique())}")
        st.write(f"**Available cancer types in data:** {len(risks_df['cause_name'].unique())}")
        st.write(f"**Available states (or districts):** {len(risks_df['location_name'].unique())}")
    
    # === FOOTER ===
    st.markdown("---")
    st.caption("Data sources: [Add your data sources] | Last updated: December 2025")