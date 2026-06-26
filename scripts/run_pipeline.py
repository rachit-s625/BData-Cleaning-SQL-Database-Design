import subprocess
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_script(script_name):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    logging.info(f"Running script: {script_name}...")
    
    try:
        result = subprocess.run([sys.executable, script_path], check=True, capture_output=True, text=True)
        logging.info(f"Finished {script_name} successfully.")
        # Log stdout if there's any important output
        if "SAMPLE FUND RECOMMENDATIONS" in result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing {script_name}: {e.stderr}")
        return False

def main():
    logging.info("Starting Mutual Fund Analytics Platform Pipeline...")
    
    steps = [
        ("live_nav_fetch.py", "Live NAV Fetching"),
        ("data_ingestion.py", "Data Ingestion & Quality Analysis"),
        ("etl_pipeline.py", "Data Cleaning & Transformation (ETL)"),
        ("load_db.py", "SQLite Database Setup & Loading"),
        ("compute_metrics.py", "Performance & Risk Metrics Computation"),
        ("recommender.py", "Composite Scorecard & Recommendation Engine"),
        ("generate_notebooks.py", "Jupyter Notebooks Generation"),
        ("generate_artifacts.py", "Presentation Deck & PDF Report Generation")
    ]
    
    for script, desc in steps:
        print(f"\n>>> [STEP] {desc}")
        success = run_script(script)
        if not success:
            logging.error(f"Pipeline failed at step: {desc} ({script}). Aborting.")
            sys.exit(1)
            
    print("\n" + "="*50)
    print("      PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("All deliverables have been generated:")
    print("  - Raw Live NAV CSV files: data/raw/")
    print("  - Cleaned & Processed CSV files: data/processed/")
    print("  - SQLite Database: data/db/bluestock_mf.db")
    print("  - SQL Schema & Queries: sql/")
    print("  - Calculated Metrics & Scorecard: data/processed/")
    print("  - Jupyter Notebooks: notebooks/")
    print("  - Interactive Dashboard: dashboard/app.py")
    print("  - Final PDF Report: reports/Final_Report.pdf")
    print("  - PowerPoint Deck: reports/Presentation.pptx")
    print("="*50)

if __name__ == "__main__":
    main()
