import altair as alt
import pandas as pd
import streamlit as st

# === VISUALIZATION 1: CANCER vs RISK FACTORS HEATMAP (sriya map) ===
    def filter_by_time(df, selected_year, year_range):
        if selected_year is not None:
            return df[df["year"] == selected_year]
        if year_range is not None:
            start = year_range[0]
            end = year_range[1]
            return df[(df["year"] >= start) & (df["year"] <= end)]
        return df

    # Filtering risks_df for selected risk factors and time
    heat_df = risks_df[risks_df["rei_name"].isin(selected_risks)]
    heat_df = filter_by_time(heat_df, selected_year=selected_year, year_range=year_range)

    # Aggregate mean value for each (cancer, risk)
    heat_df = (
        heat_df.groupby(["cause_name", "rei_name"])["val"]
        .mean()
        .reset_index()
    )

    heatmap_df = heat_df.rename(columns={"rei_name": "risk_factor"})

    # Min and Max values
    val_min = heatmap_df["val"].replace(0, 0.0001).min()
    val_max = heatmap_df["val"].max()
    
    st.header("Cancer Types vs Risk Factors")
    st.markdown("**Click on a cancer type** to update the geographic and temporal visualizations below")
    
    # Heatmap Code
    heatmap = alt.Chart(heatmap_df).mark_rect().encode(
        x = alt.X('risk_factor', title = 'Risk Factors'),
        y = alt.Y('cause_name', title = 'Cancer Type'),
        color=alt.Color('val', title="Risk Contribution",
        scale=alt.Scale(scheme="blueorange", domainMid=0)),
        tooltip=['cause_name', 'risk_factor', 'val'],
    )
    
    st.altair_chart(heatmap, use_container_width=True)

    st.markdown("---")
