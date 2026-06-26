import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def write_notebook(notebook_path, cells):
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    with open(notebook_path, "w") as f:
        json.dump(nb, f, indent=2)
    logging.info(f"Generated notebook at {notebook_path}")

def generate_all_notebooks():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    notebooks_dir = os.path.abspath(os.path.join(script_dir, "..", "notebooks"))
    os.makedirs(notebooks_dir, exist_ok=True)
    
    # 1. 01_data_ingestion.ipynb
    cells_ingestion = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 01 - Data Ingestion Phase\n",
                "This notebook loads the 10 raw CSV datasets, validates their schemas, checks for missing values, and generates a data quality report."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys\n",
                "sys.path.append('../scripts')\n",
                "import data_ingestion\n",
                "data_ingestion.main()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "import os\n",
                "df_fund = pd.read_csv('../data/raw/01_fund_master.csv')\n",
                "print('Fund Master Shape:', df_fund.shape)\n",
                "df_fund.head()"
            ]
        }
    ]
    write_notebook(os.path.join(notebooks_dir, "01_data_ingestion.ipynb"), cells_ingestion)
    
    # 2. 02_data_cleaning.ipynb
    cells_cleaning = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 02 - Data Cleaning Phase\n",
                "This notebook executes the data cleaning rules for each dataset (such as forward-filling weekends in NAV history and standardizing transaction types)."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys\n",
                "sys.path.append('../scripts')\n",
                "import etl_pipeline\n",
                "etl_pipeline.main()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "df_clean_nav = pd.read_csv('../data/processed/clean_nav_history.csv')\n",
                "print('Cleaned NAV History Shape:', df_clean_nav.shape)\n",
                "df_clean_nav.head()"
            ]
        }
    ]
    write_notebook(os.path.join(notebooks_dir, "02_data_cleaning.ipynb"), cells_cleaning)

    # 3. 03_eda_analysis.ipynb
    cells_eda = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 03 - Exploratory Data Analysis (EDA)\n",
                "This notebook performs comprehensive EDA and saves publication-quality visualization charts."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "import sqlite3\n",
                "import os\n",
                "\n",
                "# Setup plotting style\n",
                "sns.set_theme(style='whitegrid')\n",
                "plt.rcParams['figure.figsize'] = (10, 6)\n",
                "\n",
                "conn = sqlite3.connect('../data/db/bluestock_mf.db')\n",
                "df_nav = pd.read_sql('SELECT * FROM fact_nav', conn)\n",
                "df_funds = pd.read_sql('SELECT * FROM dim_fund', conn)\n",
                "df_tx = pd.read_sql('SELECT * FROM fact_transactions', conn)\n",
                "df_sip = pd.read_sql('SELECT * FROM fact_sip_industry', conn)\n",
                "\n",
                "os.makedirs('../reports/charts', exist_ok=True)\n",
                "print('Data Loaded successfully for EDA.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Chart 1: NAV Trends of Top Schemes"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "for code, group in df_nav.groupby('amfi_code'):\n",
                "    name = df_funds[df_funds['amfi_code'] == code]['scheme_name'].values[0]\n",
                "    plt.plot(pd.to_datetime(group['date']), group['nav'], label=name[:20])\n",
                "plt.title('NAV Trend Analysis (2022-2026)')\n",
                "plt.xlabel('Date')\n",
                "plt.ylabel('NAV')\n",
                "plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')\n",
                "plt.tight_layout()\n",
                "plt.savefig('../reports/charts/nav_trends.png')\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Chart 2: Transaction Type distribution"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "df_tx['transaction_type'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['#4F46E5', '#10B981', '#EF4444'])\n",
                "plt.title('Investor Transaction Type Split')\n",
                "plt.ylabel('')\n",
                "plt.savefig('../reports/charts/transaction_distribution.png')\n",
                "plt.show()"
            ]
        }
    ]
    write_notebook(os.path.join(notebooks_dir, "03_eda_analysis.ipynb"), cells_eda)
    
    # 4. 04_performance_analytics.ipynb
    cells_performance = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 04 - Fund Performance Analytics\n",
                "This notebook computes returns, CAGR, risk-adjusted returns (Sharpe, Sortino), Alpha, Beta, standard deviation, and maximum drawdowns."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys\n",
                "sys.path.append('../scripts')\n",
                "import compute_metrics\n",
                "compute_metrics.main()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "df_metrics = pd.read_csv('../data/processed/returns_computed.csv')\n",
                "df_metrics.head()"
            ]
        }
    ]
    write_notebook(os.path.join(notebooks_dir, "04_performance_analytics.ipynb"), cells_performance)
    
    # 5. 05_advanced_analytics.ipynb
    cells_advanced = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 05 - Advanced Analytics & Recommendations\n",
                "This notebook builds the composite scorecard rankings, computes Historical & Conditional VaR, Herfindahl Index (HHI) for portfolio concentration, and executes the fund recommendation engine."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys\n",
                "sys.path.append('../scripts')\n",
                "import recommender\n",
                "recommender.main()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "df_scorecard = pd.read_csv('../data/processed/fund_scorecard.csv')\n",
                "df_scorecard.head(5)"
            ]
        }
    ]
    write_notebook(os.path.join(notebooks_dir, "05_advanced_analytics.ipynb"), cells_advanced)

if __name__ == "__main__":
    generate_all_notebooks()
