import os
import sqlite3
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_database():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "db"))
    processed_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "processed"))
    sql_dir = os.path.abspath(os.path.join(script_dir, "..", "sql"))
    
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "bluestock_mf.db")
    schema_path = os.path.join(sql_dir, "schema.sql")
    
    # Reset database if exists
    if os.path.exists(db_path):
        logging.info(f"Removing old database at {db_path}...")
        os.remove(db_path)
        
    logging.info(f"Connecting to SQLite database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Execute schema.sql to create tables
    logging.info(f"Executing schema from {schema_path}...")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()
    
    # A. Load dim_fund
    df_fund = pd.read_csv(os.path.join(processed_dir, "clean_fund_master.csv"))
    df_fund.to_sql("dim_fund", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_fund)} rows into dim_fund")
    
    # B. Generate and load dim_date dynamically
    logging.info("Generating dim_date entries dynamically from multiple sources...")
    df_nav = pd.read_csv(os.path.join(processed_dir, "clean_nav_history.csv"))
    df_tx = pd.read_csv(os.path.join(processed_dir, "clean_investor_transactions.csv"))
    df_port = pd.read_csv(os.path.join(processed_dir, "clean_portfolio_holdings.csv"))
    df_aum = pd.read_csv(os.path.join(processed_dir, "clean_aum_by_fund_house.csv"))
    df_bench = pd.read_csv(os.path.join(processed_dir, "clean_benchmark_indices.csv"))
    
    nav_dates = pd.to_datetime(df_nav["date"])
    tx_dates = pd.to_datetime(df_tx["transaction_date"])
    port_dates = pd.to_datetime(df_port["portfolio_date"])
    aum_dates = pd.to_datetime(df_aum["date"])
    bench_dates = pd.to_datetime(df_bench["date"])
    
    all_dates = pd.concat([nav_dates, tx_dates, port_dates, aum_dates, bench_dates]).dropna().unique()
    all_dates = sorted(all_dates)
    
    date_records = []
    for d in all_dates:
        dt = pd.to_datetime(d)
        date_records.append({
            "date_id": int(dt.strftime("%Y%m%d")),
            "date": dt.strftime("%Y-%m-%d"),
            "year": dt.year,
            "month": dt.month,
            "quarter": (dt.month - 1) // 3 + 1,
            "is_weekday": 1 if dt.weekday() < 5 else 0
        })
    df_date = pd.DataFrame(date_records)
    df_date.to_sql("dim_date", conn, if_exists="append", index=False)
    logging.info(f"Generated and loaded {len(df_date)} rows into dim_date")
    
    # C. Load fact_nav
    df_nav["date"] = pd.to_datetime(df_nav["date"]).dt.strftime("%Y-%m-%d")
    df_nav.to_sql("fact_nav", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_nav)} rows into fact_nav")
    
    # D. Load fact_transactions
    df_tx["transaction_date"] = pd.to_datetime(df_tx["transaction_date"]).dt.strftime("%Y-%m-%d")
    df_tx.to_sql("fact_transactions", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_tx)} rows into fact_transactions")
    
    # E. Load fact_performance
    df_perf = pd.read_csv(os.path.join(processed_dir, "clean_scheme_performance.csv"))
    df_perf.to_sql("fact_performance", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_perf)} rows into fact_performance")
    
    # F. Load fact_portfolio
    df_port["portfolio_date"] = pd.to_datetime(df_port["portfolio_date"]).dt.strftime("%Y-%m-%d")
    df_port.to_sql("fact_portfolio", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_port)} rows into fact_portfolio")
    
    # G. Load fact_aum
    df_aum["date"] = pd.to_datetime(df_aum["date"]).dt.strftime("%Y-%m-%d")
    df_aum.to_sql("fact_aum", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_aum)} rows into fact_aum")
    
    # H. Load fact_sip_industry
    df_sip = pd.read_csv(os.path.join(processed_dir, "clean_monthly_sip_inflows.csv"))
    df_sip.to_sql("fact_sip_industry", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_sip)} rows into fact_sip_industry")

    # I. Load fact_category_inflows
    df_cat = pd.read_csv(os.path.join(processed_dir, "clean_category_inflows.csv"))
    df_cat.to_sql("fact_category_inflows", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_cat)} rows into fact_category_inflows")

    # J. Load fact_industry_folio_count
    df_fol = pd.read_csv(os.path.join(processed_dir, "clean_industry_folio_count.csv"))
    df_fol.to_sql("fact_industry_folio_count", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_fol)} rows into fact_industry_folio_count")

    # K. Load fact_benchmark_indices
    df_bench["date"] = pd.to_datetime(df_bench["date"]).dt.strftime("%Y-%m-%d")
    df_bench.to_sql("fact_benchmark_indices", conn, if_exists="append", index=False)
    logging.info(f"Loaded {len(df_bench)} rows into fact_benchmark_indices")
    
    conn.close()
    logging.info("Database loaded successfully.")

if __name__ == "__main__":
    load_database()
