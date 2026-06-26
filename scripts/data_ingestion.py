import os
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def analyze_dataset(file_path):
    filename = os.path.basename(file_path)
    logging.info(f"Analyzing {filename}...")
    
    try:
        df = pd.read_csv(file_path)
        
        info = {
            "filename": filename,
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_count": df.duplicated().sum(),
            "head": df.head(3).to_dict(orient="records")
        }
        
        return df, info
    except Exception as e:
        logging.error(f"Error reading {filename}: {e}")
        return None, {"filename": filename, "error": str(e)}

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "raw"))
    reports_dir = os.path.abspath(os.path.join(script_dir, "..", "reports"))
    os.makedirs(reports_dir, exist_ok=True)
    
    files = [
        "01_fund_master.csv",
        "02_nav_history.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "07_scheme_performance.csv",
        "08_investor_transactions.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv"
    ]
    
    report_content = []
    report_content.append("==================================================")
    report_content.append("          DATA QUALITY & INGESTION REPORT         ")
    report_content.append("==================================================")
    
    dfs = {}
    
    for f in files:
        file_path = os.path.join(raw_dir, f)
        if not os.path.exists(file_path):
            logging.warning(f"File {f} not found in {raw_dir}")
            report_content.append(f"\n[WARNING] File {f} is missing from raw directory.")
            continue
            
        df, info = analyze_dataset(file_path)
        if df is not None:
            dfs[f] = df
            report_content.append(f"\nFile: {info['filename']}")
            report_content.append(f"  Shape: {info['shape']}")
            report_content.append(f"  Duplicates: {info['duplicate_count']}")
            report_content.append("  Columns & Types:")
            for col, dtype in info["dtypes"].items():
                missing = info["missing_values"].get(col, 0)
                report_content.append(f"    - {col} ({dtype}): {missing} missing values")
        else:
            report_content.append(f"\nFile: {f} - FAILED TO LOAD - {info.get('error')}")

    # Cross-dataset validations
    report_content.append("\n==================================================")
    report_content.append("          CROSS-DATASET VALIDATIONS               ")
    report_content.append("==================================================")
    
    # 1. Validate AMFI code consistency between fund_master and nav_history
    if "01_fund_master.csv" in dfs and "02_nav_history.csv" in dfs:
        fm_codes = set(dfs["01_fund_master.csv"]["amfi_code"].unique())
        nav_codes = set(dfs["02_nav_history.csv"]["amfi_code"].unique())
        
        missing_in_nav = fm_codes - nav_codes
        missing_in_fm = nav_codes - fm_codes
        
        report_content.append(f"\nAMFI Code Consistency:")
        report_content.append(f"  Codes in Fund Master: {len(fm_codes)}")
        report_content.append(f"  Codes in NAV History: {len(nav_codes)}")
        report_content.append(f"  Fund Master codes missing from NAV History: {list(missing_in_nav)}")
        report_content.append(f"  NAV History codes missing from Fund Master: {len(missing_in_fm)} codes (total)")
        
    # Write report
    report_path = os.path.join(reports_dir, "data_quality_report.txt")
    with open(report_path, "w") as f_out:
        f_out.write("\n".join(report_content))
    logging.info(f"Data quality report saved to {report_path}")

if __name__ == "__main__":
    main()
