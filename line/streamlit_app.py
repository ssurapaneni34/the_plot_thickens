import streamlit as st
import pandas as pd
import altair as alt
from line import render_lineplot

# Page configuration
st.set_page_config(
    page_title="Cancer Risk Factors Across the US",
    page_icon="🔬",
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
    """Load the deaths and risks data"""
    deaths_df = pd.read_csv("../data/Deaths.csv")
    risks_df = pd.read_csv("../data/Risks.csv")
    return deaths_df, risks_df

def get_default_cancer(risks_df):
    """Get a default cancer to display (e.g., most common one)"""
    # Can change this logic to pick whatever default makes sense, right now it's Bladder
    cancers = sorted(risks_df['cause_name'].unique())
    return cancers[0] if len(cancers) > 0 else None


# Initialize session state for selected cancer
if 'selected_cancer' not in st.session_state:
    st.session_state.selected_cancer = None
    st.session_state.needs_default = True  # Flag to set default after data loads

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Main Dashboard", "About"])

if page == "About":
    st.title("About This Project")
    st.markdown("""
    ## Cancer Risk Factors Analysis
    
    ### Project Description
    
    This interactive dashboard explores how different risk factors contribute to various cancer types 
    across the United States over time. 
    
    **Data Sources:**
    - Cancer mortality data from [Data Source]
    - Risk factor data from [Data Source]
    
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
    4. Click on a cancer type to see detailed state-level and temporal analyses
    
    **Team Members:**
    [Add team member names here]
    
    **Last Updated:** December 2025
    """)

else:
    # Main Dashboard
    st.title("🔬 Cancer Risk Factors Across the US")
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
    
    # === RISK FACTOR SELECTOR ===
    st.sidebar.subheader("1. Select Risk Factors")
    
    # Quick selection buttons for categories
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        if st.button("All Environmental", use_container_width=True):
            st.session_state.selected_risks = RISK_FACTORS["Environmental"].copy()
    
    with col2:
        if st.button("All Behavioral", use_container_width=True):
            st.session_state.selected_risks = RISK_FACTORS["Behavioral"].copy()
    
    with col3:
        if st.button("All Metabolic", use_container_width=True):
            st.session_state.selected_risks = RISK_FACTORS["Metabolic"].copy()
    
    # Initialize selected_risks if not in session state
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
    
    # === TIME SELECTOR ===
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
    st.info(f"**Analyzing {len(selected_risks)} risk factor(s)** | **{time_display}** | **Cancer: {st.session_state.selected_cancer}**")
    
    if not selected_risks:
        st.warning("⚠️ Please select at least one risk factor to begin analysis")
        st.stop()
    
    # === VISUALIZATION 1: CANCER vs RISK FACTORS HEATMAP (sriya map) ===
    st.header("Cancer Types vs Risk Factors")
    st.markdown("**Click on a cancer type** to update the geographic and temporal visualizations below")
    
    # Placeholder for heatmap
    heatmap_placeholder = st.empty()
    
    with heatmap_placeholder.container():
        st.info("**Heatmap Visualization**\n\nThis will show cancer types (rows) vs selected risk factors (columns). Click on a cancer to update the visualizations below.")
        
        # Example of what will be passed to visualization component
        st.code(f"""
# Data that will be available for heatmap:
- Selected risks: {selected_risks}
- Time period: {time_display}
- Data source: risks_df filtered by selections
- Interaction: clickable cancer selection → updates st.session_state.selected_cancer
- Current selection: {st.session_state.selected_cancer} (highlighted in heatmap)
        """)
    
    st.markdown("---")
    
    # === VISUALIZATIONS 2 & 3 (NEED TO DEFAULT TO A SPECIFIC CANCER) ===
    st.markdown(f"### Detailed Analysis: **{st.session_state.selected_cancer}**")
    st.caption("Click a different cancer in the heatmap above to update these visualizations")
    
    # Create two columns for the detailed views
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Geographic Distribution (ryan map)")
        st.caption(f"Risk factors for {st.session_state.selected_cancer} across US states")
        
        # Placeholder for state map
        map_placeholder = st.empty()
        
        with map_placeholder.container():
            st.info("**US State Map**\n\nHoverable map showing selected risk factors by state. Colors indicate risk levels.")
            
            st.code(f"""
# Data for map visualization:
- Cancer: {st.session_state.selected_cancer}
- Risk factors: {selected_risks}
- Time: {time_display}
- Interaction: hover to see state-specific values
            """)
    
    with col2:
        st.subheader("Temporal Trends (jack map)")
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

        selected_cancer = st.selectbox(
            "Choose a cancer type:",
            options=cancer_list,
            index=cancer_list.index(st.session_state.selected_cancer),
            key="cancer_select",
        )

        # Keep session_state in sync with the widget
        st.session_state.selected_cancer = selected_cancer
        ####

        
        
        ### Placeholder for line chart
        #line_placeholder = st.empty()
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
        st.write(f"**Available states:** {len(risks_df['location_name'].unique())}")
    
    # === FOOTER ===
    st.markdown("---")
    st.caption("Data sources: [Add your data sources] | Last updated: December 2025")

# === HELPER FUNCTIONS FOR TEAM ===
# These functions can be imported by other visualization modules

def get_filtered_data(risks_df, selected_risks, year=None, year_range=None):
    """
    Filter the risks dataframe based on selections.
    
    Parameters:
    - risks_df: full risks dataframe
    - selected_risks: list of risk factor names
    - year: single year (int) or None
    - year_range: tuple of (start_year, end_year) or None
    
    Returns:
    - filtered dataframe
    """
    filtered = risks_df[risks_df['rei_name'].isin(selected_risks)]
    
    if year is not None:
        filtered = filtered[filtered['year'] == year]
    elif year_range is not None:
        filtered = filtered[(filtered['year'] >= year_range[0]) & 
                          (filtered['year'] <= year_range[1])]
    
    return filtered

def get_cancer_list(risks_df):
    """Get unique list of cancer types from data"""
    return sorted(risks_df['cause_name'].unique())

def get_state_list(risks_df):
    """Get unique list of states from data"""
    return sorted(risks_df['location_name'].unique())