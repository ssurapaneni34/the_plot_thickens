# line.py
import streamlit as st
import altair as alt
import pandas as pd


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

    ###
    #st.markdown("### data preview - before filter")
    #st.dataframe(df.head(), use_container_width=True)

    # Filter by selected risk factors
    df = df[df["rei_name"].isin(selected_risks)]

    df["year"] = df["year"].astype(int)
    df["val"] = df["val"].astype(float)

    # Filter by time
    if selected_year is not None:
        df = df[df["year"] == selected_year]
    elif year_range is not None:
        df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    ###
    #st.markdown("### data preview")
    #st.dataframe(df.head(), use_container_width=True)
    #st.write("Year column dtype:", df["val"].dtype)
    

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
            y=alt.Y("val:Q", title="Mean value of DALYS from risk factor"),
            color=alt.Color("rei_name:N", title="Risk factor"),
            tooltip=[
                alt.Tooltip("year:O", title="Year"),
                alt.Tooltip("rei_name:N", title="Risk factor"),
                alt.Tooltip("val:Q", title="Mean val", format=".2f"),
            ],
        )
        .properties(
            height=350,
            title=f"Temporal trends for {selected_cancer}\n{time_display}",
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)
