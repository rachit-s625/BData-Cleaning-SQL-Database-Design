# Bluestock Mutual Fund Analytics Platform
An end-to-end data engineering, ETL, and analytics platform built for Bluestock Fintech.

This project ingests 10 distinct mutual fund datasets and live API data from `mfapi.in`, cleans and validates the schemas, stores the results in a relational SQLite database star schema, calculates advanced performance/risk metrics, and presents interactive insights via a Streamlit dashboard.

---

## Folder Structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/                 # Original CSVs and live downloaded NAVs
│   ├── processed/           # Cleaned CSV files and computed metrics
│   └── db/                  # SQLite relational database (bluestock_mf.db)
│
├── notebooks/               # Step-by-step Jupyter Notebooks (01 to 05)
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
│
├── scripts/                 # Modular Python pipeline scripts
│   ├── data_ingestion.py    # Analyzes raw data quality
│   ├── live_nav_fetch.py    # Downloads live NAVs from API
│   ├── etl_pipeline.py      # Cleans and standardizes raw CSVs
│   ├── load_db.py           # Loads SQL tables and populates dim_date
│   ├── compute_metrics.py   # Computes financial risk-return ratios (CAGR, Sharpe, etc.)
│   ├── recommender.py       # Scorecard ranks and risk profile recommendations
│   ├── generate_notebooks.py# Programmatic notebook creator
│   ├── generate_artifacts.py# Generates final PDF report and PowerPoint presentation
│   └── run_pipeline.py      # Master orchestrator script
│
├── sql/                     # Database scripts
│   ├── schema.sql           # SQLite table structures and indexes
│   └── queries.sql          # 10 analytical queries
│
├── dashboard/               # Streamlit application folder
│   └── app.py               # Interactive dashboard source code
│
├── reports/                 # Quality reports, SQL results, PDF, and PPTX decks
│   ├── Final_Report.pdf
│   └── Presentation.pptx
│
├── requirements.txt         # Package dependencies
└── .gitignore               # Excluded file paths
```

---

## Installation & Setup

1. **Clone/Navigate** to the capstone directory:
   ```bash
   cd bluestock_mf_capstone
   ```

2. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

---

## How to Run

### 1. Run the End-to-End Pipeline
Execute the master runner to perform ingestion, live fetching, cleaning, database storage, metrics computation, notebook creation, and report generation in a single command:
```bash
python3 scripts/run_pipeline.py
```

### 2. Launch the Streamlit Dashboard
Launch the web interface locally to view interactive charts, fund scorecard, and cohort demographics:
```bash
streamlit run dashboard/app.py
```

---

## Database Architecture
The relational model matches a **Star Schema** with:
- **`dim_fund`**: Scheme codes, AMCs, categorization, expense ratios, risk grades, and launch parameters.
- **`dim_date`**: Unified date index mapping calendar details (day, month, year, quarter, weekday status).
- **`fact_nav`**: Chronological daily NAVs and calculated returns.
- **`fact_transactions`**: Demographic segmentations, transaction splits (SIP vs Lumpsum), states, and payment details.
- **`fact_performance`**: 1yr/3yr/5yr returns, Sharpe, Sortino, Alpha, Beta, maximum drawdowns, and rankings.
- **`fact_portfolio`**: Equity weight allocations and sector metrics.
- **`fact_aum`**: Asset Under Management trends per fund house.
- **`fact_sip_industry`**: Inflow metrics and folio growth rates.
