import os
import pandas as pd
import numpy as np
import sqlite3
from scipy.stats import linregress
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def compute_financial_metrics(conn, processed_dir):
    logging.info("Computing fund performance & risk metrics...")
    
    # Load data from database
    df_nav = pd.read_sql("SELECT * FROM fact_nav", conn)
    df_funds = pd.read_sql("SELECT * FROM dim_fund", conn)
    df_bench = pd.read_sql("SELECT * FROM fact_benchmark_indices", conn)
    
    # Parse dates
    df_nav["date"] = pd.to_datetime(df_nav["date"])
    df_bench["date"] = pd.to_datetime(df_bench["date"])
    
    # Calculate daily returns for benchmarks
    df_bench = df_bench.sort_values(["index_name", "date"])
    df_bench["daily_return_pct"] = df_bench.groupby("index_name")["close_value"].pct_change() * 100
    df_bench["daily_return_pct"] = df_bench["daily_return_pct"].fillna(0.0)
    
    metrics_list = []
    
    # We will compute metrics for all funds
    for code, group in df_nav.groupby("amfi_code"):
        group = group.sort_values("date")
        fund_info = df_funds[df_funds["amfi_code"] == code]
        if fund_info.empty:
            continue
        fund_name = fund_info.iloc[0]["scheme_name"]
        bench_name = fund_info.iloc[0]["benchmark"]
        
        # Filter benchmark data
        bench_group = df_bench[df_bench["index_name"] == bench_name].sort_values("date")
        
        # Calculate daily returns for fund
        fund_returns = group["daily_return_pct"].values
        
        # 1. Standard Deviation (Annualized)
        std_dev = np.std(fund_returns) * np.sqrt(252) if len(fund_returns) > 1 else 0.0
        
        # 2. Annualized Return (Mean return * 252)
        ann_return = np.mean(group["daily_return_pct"]) * 252 if len(fund_returns) > 0 else 0.0
        
        # 3. CAGR calculations
        cagr_1yr, cagr_3yr, cagr_5yr = 0.0, 0.0, 0.0
        max_date = group["date"].max()
        
        def calc_cagr(start_date, end_date):
            sub = group[(group["date"] >= start_date) & (group["date"] <= end_date)]
            if len(sub) < 30:
                return 0.0
            nav_start = sub.iloc[0]["nav"]
            nav_end = sub.iloc[-1]["nav"]
            years = (sub["date"].max() - sub["date"].min()).days / 365.25
            if years <= 0:
                return 0.0
            return (nav_end / nav_start) ** (1.0 / years) - 1.0
            
        cagr_1yr = calc_cagr(max_date - pd.Timedelta(days=365), max_date) * 100
        cagr_3yr = calc_cagr(max_date - pd.Timedelta(days=3*365), max_date) * 100
        cagr_5yr = calc_cagr(max_date - pd.Timedelta(days=5*365), max_date) * 100
        
        # 4. Sharpe Ratio (Rf = 6.5%)
        Rf = 6.5
        sharpe = (ann_return - Rf) / std_dev if std_dev > 0 else 0.0
        
        # 5. Sortino Ratio
        neg_returns = fund_returns[fund_returns < 0]
        downside_std = np.std(neg_returns) * np.sqrt(252) if len(neg_returns) > 1 else 0.0
        sortino = (ann_return - Rf) / downside_std if downside_std > 0 else 0.0
        
        # 6. Max Drawdown
        nav_series = group["nav"].values
        running_max = np.maximum.accumulate(nav_series)
        drawdowns = nav_series / running_max - 1.0
        max_dd = np.min(drawdowns) * 100 if len(drawdowns) > 0 else 0.0
        
        # 7. Alpha, Beta, Tracking Error & Information Ratio vs Benchmark
        alpha, beta, tracking_error, info_ratio = 0.0, 1.0, 0.0, 0.0
        
        # Align dates with benchmark
        merged = pd.merge(group[["date", "daily_return_pct"]], 
                          bench_group[["date", "daily_return_pct"]], 
                          on="date", suffixes=("_fund", "_bench"))
                          
        if len(merged) > 30:
            fund_aligned = merged["daily_return_pct_fund"].values
            bench_aligned = merged["daily_return_pct_bench"].values
            
            # Regression for Alpha/Beta
            slope, intercept, _, _, _ = linregress(bench_aligned, fund_aligned)
            beta = slope
            alpha = intercept * 252
            
            # Tracking Error (Annualized standard deviation of active return)
            active_return = fund_aligned - bench_aligned
            tracking_error = np.std(active_return) * np.sqrt(252)
            
            # Information Ratio
            ann_bench_return = np.mean(bench_aligned) * 252
            info_ratio = (ann_return - ann_bench_return) / tracking_error if tracking_error > 0 else 0.0
            
        metrics_list.append({
            "amfi_code": code,
            "scheme_name": fund_name,
            "annualized_return_pct": ann_return,
            "std_dev_ann_pct": std_dev,
            "cagr_1yr_pct": cagr_1yr,
            "cagr_3yr_pct": cagr_3yr,
            "cagr_5yr_pct": cagr_5yr,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown_pct": max_dd,
            "alpha": alpha,
            "beta": beta,
            "tracking_error_pct": tracking_error,
            "information_ratio": info_ratio
        })
        
    df_metrics = pd.DataFrame(metrics_list)
    df_metrics.to_csv(os.path.join(processed_dir, "returns_computed.csv"), index=False)
    logging.info(f"Saved performance metrics to returns_computed.csv")
    
    # Save CAGR report separately
    df_cagr = df_metrics[["amfi_code", "scheme_name", "cagr_1yr_pct", "cagr_3yr_pct", "cagr_5yr_pct"]]
    df_cagr.to_csv(os.path.join(processed_dir, "cagr_report.csv"), index=False)
    
    # Save individual risk sheets
    df_metrics[["amfi_code", "scheme_name", "sharpe_ratio"]].to_csv(os.path.join(processed_dir, "sharpe_values.csv"), index=False)
    df_metrics[["amfi_code", "scheme_name", "sortino_ratio"]].to_csv(os.path.join(processed_dir, "sortino_values.csv"), index=False)
    df_metrics[["amfi_code", "scheme_name", "alpha", "beta"]].to_csv(os.path.join(processed_dir, "alpha_beta.csv"), index=False)
    df_metrics[["amfi_code", "scheme_name", "max_drawdown_pct"]].to_csv(os.path.join(processed_dir, "max_drawdown.csv"), index=False)
    
    return df_metrics

def compute_advanced_analytics(conn, processed_dir):
    logging.info("Computing advanced analytics & risk metrics (VaR, HHI, Cohort)...")
    
    # 1. Historical VaR and CVaR
    df_nav = pd.read_sql("SELECT amfi_code, daily_return_pct FROM fact_nav", conn)
    var_records = []
    
    for code, group in df_nav.groupby("amfi_code"):
        returns = group["daily_return_pct"].values
        if len(returns) < 30:
            continue
        # 95% Historical VaR (5th percentile of daily returns)
        var_95 = np.percentile(returns, 5)
        # CVaR (mean of returns below VaR)
        cvar_95 = np.mean(returns[returns <= var_95])
        
        var_records.append({
            "amfi_code": code,
            "historical_var_95_pct": var_95,
            "cvar_95_pct": cvar_95
        })
        
    df_var = pd.DataFrame(var_records)
    df_var.to_csv(os.path.join(processed_dir, "var_cvar_report.csv"), index=False)
    
    # 2. Herfindahl Index (HHI) for Sector Concentration
    df_port = pd.read_sql("SELECT amfi_code, sector, weight_pct FROM fact_portfolio", conn)
    hhi_records = []
    for code, group in df_port.groupby("amfi_code"):
        # Aggregate by sector
        sector_weights = group.groupby("sector")["weight_pct"].sum()
        # HHI = sum(w_i^2) where w_i is weight in percent (e.g. 20% weight -> 20^2 = 400)
        hhi = np.sum(sector_weights ** 2)
        hhi_records.append({
            "amfi_code": code,
            "sector_hhi": hhi
        })
    df_hhi = pd.DataFrame(hhi_records)
    df_hhi.to_csv(os.path.join(processed_dir, "sector_hhi.csv"), index=False)
    
    # 3. Investor Cohort Analysis
    df_tx = pd.read_sql("SELECT * FROM fact_transactions", conn)
    df_tx["transaction_date"] = pd.to_datetime(df_tx["transaction_date"])
    
    # Find first transaction date for each investor to assign cohort
    first_tx = df_tx.groupby("investor_id")["transaction_date"].min().reset_index()
    first_tx["cohort_year"] = first_tx["transaction_date"].dt.year
    
    # Merge cohort info back
    df_tx = pd.merge(df_tx, first_tx[["investor_id", "cohort_year"]], on="investor_id")
    
    cohort_summary = df_tx.groupby("cohort_year").agg(
        total_invested_inr=("amount_inr", "sum"),
        avg_transaction_amount=("amount_inr", "mean"),
        active_investors=("investor_id", "nunique")
    ).reset_index()
    cohort_summary.to_csv(os.path.join(processed_dir, "cohort_analysis.csv"), index=False)
    
    # 4. SIP Continuation Analysis
    # Get all SIP transactions
    df_sip = df_tx[df_tx["transaction_type"] == "SIP"].sort_values(["investor_id", "transaction_date"])
    sip_counts = df_sip["investor_id"].value_counts()
    eligible_investors = sip_counts[sip_counts >= 6].index
    
    continuity_records = []
    for inv_id in eligible_investors:
        inv_group = df_sip[df_sip["investor_id"] == inv_id]
        # Calculate diff between consecutive transaction dates
        gaps = inv_group["transaction_date"].diff().dt.days.dropna()
        avg_gap = gaps.mean()
        max_gap = gaps.max()
        status = "Active" if max_gap <= 35 else "At-Risk"
        continuity_records.append({
            "investor_id": inv_id,
            "avg_gap_days": avg_gap,
            "max_gap_days": max_gap,
            "status": status
        })
    df_cont = pd.DataFrame(continuity_records)
    df_cont.to_csv(os.path.join(processed_dir, "sip_continuity.csv"), index=False)
    logging.info("Advanced metrics calculation complete.")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(script_dir, "..", "data", "db", "bluestock_mf.db"))
    processed_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "processed"))
    
    conn = sqlite3.connect(db_path)
    compute_financial_metrics(conn, processed_dir)
    compute_advanced_analytics(conn, processed_dir)
    conn.close()

if __name__ == "__main__":
    main()
