import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure Streamlit page layout
st.set_page_config(page_title="Bluestock Mutual Fund Analytics", layout="wide")

# Helper function to get database connection
def get_db_connection():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(script_dir, "..", "data", "db", "bluestock_mf.db"))
    return sqlite3.connect(db_path)

# Custom branding CSS
st.markdown("""
    <style>
    .main-title {
        color: #0F2C59;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #E28F22;
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .kpi-val {
        color: #0F2C59;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .kpi-lbl {
        color: #64748b;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">BLUESTOCK FINTECH</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Mutual Fund Analytics Platform • Capstone Dashboard</div>', unsafe_allow_html=True)

# Navigation
page = st.sidebar.radio("Navigate", ["Industry Overview", "Fund Performance", "Investor Analytics", "SIP & Market Trends"])

conn = get_db_connection()

if page == "Industry Overview":
    st.header("Industry Overview")
    
    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="kpi-card"><div class="kpi-val">Rs. 81 L Cr</div><div class="kpi-lbl">Total Industry AUM</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="kpi-card"><div class="kpi-val">Rs. 31,002 Cr</div><div class="kpi-lbl">Monthly SIP Inflow</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="kpi-card"><div class="kpi-val">26.12 Cr</div><div class="kpi-lbl">Investor Folios</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="kpi-card"><div class="kpi-val">1,908</div><div class="kpi-lbl">Active Schemes</div></div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Load AUM trends
    df_aum = pd.read_sql("SELECT * FROM fact_aum", conn)
    df_aum["date"] = pd.to_datetime(df_aum["date"])
    
    # 1. Total Industry AUM over time
    df_industry_aum = df_aum.groupby("date")["aum_crore"].sum().reset_index()
    fig_line = px.line(
        df_industry_aum, x="date", y="aum_crore",
        title="Industry AUM Growth (2022 - 2025)",
        labels={"date": "Timeline", "aum_crore": "AUM (Rs. Crore)"},
        color_discrete_sequence=["#0F2C59"]
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
    # 2. Top Fund Houses by AUM
    df_top_houses = df_aum[df_aum["date"] == df_aum["date"].max()].sort_values("aum_crore", ascending=False).head(10)
    fig_bar = px.bar(
        df_top_houses, x="aum_crore", y="fund_house", orientation="h",
        title="Top 10 Fund Houses by AUM",
        labels={"aum_crore": "AUM (Rs. Crore)", "fund_house": "Fund House"},
        color="aum_crore", color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

elif page == "Fund Performance":
    st.header("Fund Performance & Scoring")
    
    # Sidebar Filters
    st.sidebar.subheader("Filters")
    df_scorecard = pd.read_sql("SELECT * FROM fact_scorecard", conn)
    
    f_house = st.sidebar.multiselect("Fund House", options=df_scorecard["fund_house"].unique())
    f_cat = st.sidebar.multiselect("Category", options=df_scorecard["category"].unique())
    f_plan = st.sidebar.multiselect("Plan", options=df_scorecard["plan"].unique())
    
    # Filter DataFrame
    df_filtered = df_scorecard.copy()
    if f_house:
        df_filtered = df_filtered[df_filtered["fund_house"].isin(f_house)]
    if f_cat:
        df_filtered = df_filtered[df_filtered["category"].isin(f_cat)]
    if f_plan:
        df_filtered = df_filtered[df_filtered["plan"].isin(f_plan)]
        
    # 1. Risk vs Return Scatter Plot
    fig_scatter = px.scatter(
        df_filtered, x="std_dev_ann_pct", y="return_3yr_pct",
        size="composite_score", color="risk_category", hover_name="scheme_name",
        title="Risk (StdDev) vs Return (3-Year CAGR) Bubble Chart",
        labels={"std_dev_ann_pct": "Risk (Annualized Standard Deviation %)", "return_3yr_pct": "Return (3-Year CAGR %)"},
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # 2. Scorecard Table
    st.subheader("Sortable Fund Scorecard")
    st.dataframe(df_filtered[["rank", "scheme_name", "category", "return_3yr_pct", "sharpe_ratio", "alpha", "expense_ratio_pct", "composite_score"]].sort_values("rank"))
    
    # 3. NAV vs Benchmark Comparison
    st.subheader("Historical NAV Comparison vs Benchmark")
    selected_scheme = st.selectbox("Select Scheme to view NAV Trend", options=df_filtered["scheme_name"].unique())
    if selected_scheme:
        code = df_scorecard[df_scorecard["scheme_name"] == selected_scheme]["amfi_code"].values[0]
        benchmark = df_scorecard[df_scorecard["scheme_name"] == selected_scheme]["benchmark"].values[0]
        
        df_nav = pd.read_sql(f"SELECT date, nav FROM fact_nav WHERE amfi_code = {code}", conn)
        df_bench = pd.read_sql(f"SELECT date, close_value FROM fact_benchmark_indices WHERE index_name = '{benchmark}'", conn)
        
        df_nav["date"] = pd.to_datetime(df_nav["date"])
        df_bench["date"] = pd.to_datetime(df_bench["date"])
        
        # Merge and normalize to 100 for comparison
        df_comp = pd.merge(df_nav, df_bench, on="date", how="inner").sort_values("date")
        if not df_comp.empty:
            df_comp["normalized_nav"] = (df_comp["nav"] / df_comp["nav"].iloc[0]) * 100
            df_comp["normalized_bench"] = (df_comp["close_value"] / df_comp["close_value"].iloc[0]) * 100
            
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(x=df_comp["date"], y=df_comp["normalized_nav"], name=f"{selected_scheme} (NAV)", line=dict(color="#0F2C59")))
            fig_comp.add_trace(go.Scatter(x=df_comp["date"], y=df_comp["normalized_bench"], name=f"{benchmark} (Benchmark)", line=dict(color="#E28F22", dash="dash")))
            fig_comp.update_layout(title=f"NAV vs Benchmark (Normalized to 100)", xaxis_title="Date", yaxis_title="Normalized Value")
            st.plotly_chart(fig_comp, use_container_width=True)

elif page == "Investor Analytics":
    st.header("Investor Demographics & Transaction Analytics")
    
    # Load transactions
    df_tx = pd.read_sql("SELECT * FROM fact_transactions", conn)
    
    # Filters
    st.sidebar.subheader("Filters")
    f_state = st.sidebar.multiselect("State", options=df_tx["state"].dropna().unique())
    f_age = st.sidebar.multiselect("Age Group", options=df_tx["age_group"].dropna().unique())
    f_tier = st.sidebar.multiselect("City Tier", options=df_tx["city_tier"].dropna().unique())
    
    df_tx_filt = df_tx.copy()
    if f_state:
        df_tx_filt = df_tx_filt[df_tx_filt["state"].isin(f_state)]
    if f_age:
        df_tx_filt = df_tx_filt[df_tx_filt["age_group"].isin(f_age)]
    if f_tier:
        df_tx_filt = df_tx_filt[df_tx_filt["city_tier"].isin(f_tier)]
        
    c1, c2 = st.columns(2)
    with c1:
        # State-wise investment amount
        df_state = df_tx_filt.groupby("state")["amount_inr"].sum().reset_index()
        fig_state = px.bar(
            df_state.sort_values("amount_inr", ascending=True), 
            x="amount_inr", y="state", orientation="h",
            title="Total Transaction Amount by State",
            labels={"amount_inr": "Amount (INR)", "state": "State"},
            color="amount_inr", color_continuous_scale="Purples"
        )
        st.plotly_chart(fig_state, use_container_width=True)
        
    with c2:
        # Donut Chart for Transaction Type split
        df_type = df_tx_filt.groupby("transaction_type")["amount_inr"].sum().reset_index()
        fig_donut = px.pie(
            df_type, values="amount_inr", names="transaction_type", hole=0.4,
            title="Transaction split: SIP vs Lumpsum vs Redemption",
            color_discrete_sequence=["#10B981", "#3B82F6", "#EF4444"]
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        
    c3, c4 = st.columns(2)
    with c3:
        # Age group vs avg SIP amount
        df_age = df_tx_filt[df_tx_filt["transaction_type"] == "SIP"].groupby("age_group")["amount_inr"].mean().reset_index()
        fig_age = px.bar(
            df_age, x="age_group", y="amount_inr",
            title="Average Monthly SIP Amount by Age Group",
            labels={"amount_inr": "Average Amount (INR)", "age_group": "Age Group"},
            color_discrete_sequence=["#E28F22"]
        )
        st.plotly_chart(fig_age, use_container_width=True)
        
    with c4:
        # Monthly transaction volume
        df_tx_filt["month"] = pd.to_datetime(df_tx_filt["transaction_date"]).dt.strftime("%Y-%m")
        df_vol = df_tx_filt.groupby("month")["amount_inr"].sum().reset_index()
        fig_vol = px.line(
            df_vol.sort_values("month"), x="month", y="amount_inr",
            title="Monthly Transaction Value Trend",
            labels={"month": "Month", "amount_inr": "Value (INR)"},
            color_discrete_sequence=["#10B981"]
        )
        st.plotly_chart(fig_vol, use_container_width=True)

elif page == "SIP & Market Trends":
    st.header("Industry SIP Trends & Market Benchmarks")
    
    # 1. Dual-axis: SIP Inflows (bar) + Nifty 50 (line)
    df_sip = pd.read_sql("SELECT * FROM fact_sip_industry", conn)
    df_nifty = pd.read_sql("SELECT date, close_value FROM fact_benchmark_indices WHERE index_name = 'Nifty 50'", conn)
    df_nifty["month"] = pd.to_datetime(df_nifty["date"]).dt.strftime("%Y-%m")
    df_nifty_monthly = df_nifty.groupby("month")["close_value"].mean().reset_index()
    
    df_trend = pd.merge(df_sip, df_nifty_monthly, on="month", how="inner").sort_values("month")
    
    fig_dual = go.Figure()
    # Add Bar chart for SIP inflows
    fig_dual.add_trace(go.Bar(
        x=df_trend["month"], y=df_trend["sip_inflow_crore"],
        name="SIP Inflows (Rs. Crore)", yaxis="y",
        marker_color="#3B82F6"
    ))
    # Add Line chart for Nifty 50
    fig_dual.add_trace(go.Scatter(
        x=df_trend["month"], y=df_trend["close_value"],
        name="Nifty 50 Index (Avg Close)", yaxis="y2",
        line=dict(color="#EF4444", width=3)
    ))
    
    fig_dual.update_layout(
        title="SIP Inflows vs Nifty 50 Index Performance",
        yaxis=dict(title="SIP Inflows (Rs. Crore)", titlefont=dict(color="#3B82F6"), tickfont=dict(color="#3B82F6")),
        yaxis2=dict(title="Nifty 50 Index Value", titlefont=dict(color="#EF4444"), tickfont=dict(color="#EF4444"), overlaying="y", side="right"),
        legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_dual, use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        # Category Inflow Heatmap
        df_cat = pd.read_sql("SELECT * FROM fact_category_inflows", conn)
        df_pivot = df_cat.pivot(index="category", columns="month", values="net_inflow_crore").fillna(0.0)
        fig_heat = px.imshow(
            df_pivot, 
            labels=dict(x="Month", y="Fund Category", color="Net Inflow (Cr)"),
            title="Monthly Net Category Inflows Heatmap (FY 2024-25)",
            color_continuous_scale="RdYlGn"
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
    with c2:
        # Top 5 Categories by Inflow
        df_cat_total = df_cat.groupby("category")["net_inflow_crore"].sum().reset_index()
        fig_top_cat = px.bar(
            df_cat_total.sort_values("net_inflow_crore", ascending=False).head(5),
            x="category", y="net_inflow_crore",
            title="Top 5 Categories by Net Inflow (Rs. Crore)",
            color="net_inflow_crore", color_continuous_scale="Teal"
        )
        st.plotly_chart(fig_top_cat, use_container_width=True)

conn.close()
