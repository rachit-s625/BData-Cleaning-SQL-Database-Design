import os
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def clean_fund_master(df):
    logging.info("Cleaning fund master data...")
    # Strip whitespaces from string columns
    string_cols = ["fund_house", "scheme_name", "category", "sub_category", "plan", "benchmark", "fund_manager", "risk_category"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    # Handle launch_date
    if "launch_date" in df.columns:
        df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
        
    # Handle expense ratio and exit load
    df["expense_ratio_pct"] = pd.to_numeric(df["expense_ratio_pct"], errors="coerce").fillna(0.0)
    df["exit_load_pct"] = pd.to_numeric(df["exit_load_pct"], errors="coerce").fillna(0.0)
    
    # Drop duplicates
    df = df.drop_duplicates(subset=["amfi_code"])
    return df

def clean_nav_history(df):
    logging.info("Cleaning NAV history data...")
    # Convert dates and sort
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date", "amfi_code", "nav"])
    
    # Sort
    df = df.sort_values(by=["amfi_code", "date"])
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    
    # Validate NAV > 0
    df = df[df["nav"] > 0]
    
    # Forward fill missing dates (weekends/holidays) for each fund
    cleaned_dfs = []
    for code, group in df.groupby("amfi_code"):
        group = group.set_index("date")
        # Generate full date range from min to max date in the dataset
        full_range = pd.date_range(start=group.index.min(), end=group.index.max(), freq="D")
        group = group.reindex(full_range)
        group["amfi_code"] = code
        # Forward fill NAV values
        group["nav"] = group["nav"].ffill()
        group = group.reset_index().rename(columns={"index": "date"})
        cleaned_dfs.append(group)
        
    df_cleaned = pd.concat(cleaned_dfs, ignore_index=True)
    
    # Calculate daily returns
    df_cleaned["daily_return_pct"] = df_cleaned.groupby("amfi_code")["nav"].pct_change() * 100
    df_cleaned["daily_return_pct"] = df_cleaned["daily_return_pct"].fillna(0.0)
    
    return df_cleaned

def clean_investor_transactions(df):
    logging.info("Cleaning investor transactions data...")
    # Convert date
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["transaction_date", "investor_id", "amfi_code"])
    
    # Standardize transaction_type
    df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.capitalize()
    df["transaction_type"] = df["transaction_type"].replace({
        "Sip": "SIP",
        "Lumpsum": "Lumpsum",
        "Redemption": "Redemption"
    })
    
    # Validate amounts > 0
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")
    df = df[df["amount_inr"] > 0]
    
    # KYC and payment mode validation
    df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.capitalize().replace({"Verified": "Verified", "Pending": "Pending"})
    df["payment_mode"] = df["payment_mode"].astype(str).str.strip().str.upper()
    
    # Drop duplicates
    df = df.drop_duplicates()
    return df

def clean_scheme_performance(df):
    logging.info("Cleaning scheme performance data...")
    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", 
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", 
        "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            
    df["morningstar_rating"] = pd.to_numeric(df["morningstar_rating"], errors="coerce").fillna(3).astype(int)
    df = df.drop_duplicates(subset=["amfi_code"])
    return df

def clean_generic(df, filename):
    logging.info(f"Cleaning generic dataset {filename}...")
    # Remove complete duplicates
    df = df.drop_duplicates()
    # Strip whitespaces from column names
    df.columns = df.columns.str.strip()
    return df

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "raw"))
    processed_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "processed"))
    os.makedirs(processed_dir, exist_ok=True)
    
    files = {
        "01_fund_master.csv": clean_fund_master,
        "02_nav_history.csv": clean_nav_history,
        "03_aum_by_fund_house.csv": lambda df: clean_generic(df, "03_aum_by_fund_house.csv"),
        "04_monthly_sip_inflows.csv": lambda df: clean_generic(df, "04_monthly_sip_inflows.csv"),
        "05_category_inflows.csv": lambda df: clean_generic(df, "05_category_inflows.csv"),
        "06_industry_folio_count.csv": lambda df: clean_generic(df, "06_industry_folio_count.csv"),
        "07_scheme_performance.csv": clean_scheme_performance,
        "08_investor_transactions.csv": clean_investor_transactions,
        "09_portfolio_holdings.csv": lambda df: clean_generic(df, "09_portfolio_holdings.csv"),
        "10_benchmark_indices.csv": lambda df: clean_generic(df, "10_benchmark_indices.csv")
    }
    
    for filename, clean_func in files.items():
        raw_path = os.path.join(raw_dir, filename)
        if not os.path.exists(raw_path):
            logging.error(f"Raw file {filename} does not exist!")
            continue
            
        df = pd.read_csv(raw_path)
        df_cleaned = clean_func(df)
        
        processed_path = os.path.join(processed_dir, f"clean_{filename.split('_', 1)[-1]}")
        df_cleaned.to_csv(processed_path, index=False)
        logging.info(f"Successfully cleaned and exported to {processed_path}")

if __name__ == "__main__":
    main()
