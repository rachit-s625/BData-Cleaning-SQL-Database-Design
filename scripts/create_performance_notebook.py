import os
import json

def generate_notebook():
    notebook_path = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/notebooks/Performance_Analytics.ipynb"
    
    cells = [
        # Title
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Mutual Fund Performance Analytics\n",
                "This notebook implements the complete Performance Analytics module for the Mutual Fund Analytics Platform.\n",
                "It loads and validates raw datasets, computes daily returns, CAGR, Sharpe and Sortino ratios, Alpha and Beta against Nifty 100, maximum drawdowns, tracking errors, and builds a composite fund scorecard."
            ]
        },
        # Setup/Imports
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import pandas as pd\n",
                "import numpy as np\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "from scipy.stats import linregress, skew, kurtosis\n",
                "\n",
                "# Set style for plotting\n",
                "sns.set_theme(style=\"whitegrid\")\n",
                "plt.rcParams['figure.figsize'] = (12, 6)\n",
                "print(\"Libraries imported successfully.\")"
            ]
        },
        # Step 1: Loading & Validation
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Load Required Datasets and Validate\n",
                "We load and validate the following raw datasets:\n",
                "- **Fund Master** (`01_fund_master.csv`)\n",
                "- **NAV History** (`02_nav_history.csv`)\n",
                "- **Scheme Performance** (`07_scheme_performance.csv`)\n",
                "- **Benchmark Indices** (`10_benchmark_indices.csv`)\n",
                "\n",
                "We perform checking for missing values, duplicates, verify AMFI codes, ensure benchmark dates align, and validate numeric columns."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "raw_dir = '../data/raw'\n",
                "\n",
                "fund_master = pd.read_csv(os.path.join(raw_dir, '01_fund_master.csv'))\n",
                "nav_history = pd.read_csv(os.path.join(raw_dir, '02_nav_history.csv'))\n",
                "scheme_performance = pd.read_csv(os.path.join(raw_dir, '07_scheme_performance.csv'))\n",
                "benchmark_indices = pd.read_csv(os.path.join(raw_dir, '10_benchmark_indices.csv'))\n",
                "\n",
                "print(\"--- Dataset Shapes ---\")\n",
                "print(f\"Fund Master: {fund_master.shape}\")\n",
                "print(f\"NAV History: {nav_history.shape}\")\n",
                "print(f\"Scheme Performance: {scheme_performance.shape}\")\n",
                "print(f\"Benchmark Indices: {benchmark_indices.shape}\\n\")\n",
                "\n",
                "# Missing values\n",
                "print(\"--- Missing Values Check ---\")\n",
                "print(f\"Fund Master missing values:\\n{fund_master.isnull().sum()}\\n\")\n",
                "\n",
                "# Remove duplicates\n",
                "fund_master = fund_master.drop_duplicates()\n",
                "nav_history = nav_history.drop_duplicates()\n",
                "scheme_performance = scheme_performance.drop_duplicates()\n",
                "benchmark_indices = benchmark_indices.drop_duplicates()\n",
                "\n",
                "# Date conversions\n",
                "nav_history['date'] = pd.to_datetime(nav_history['date'])\n",
                "benchmark_indices['date'] = pd.to_datetime(benchmark_indices['date'])\n",
                "fund_master['launch_date'] = pd.to_datetime(fund_master['launch_date'])\n",
                "\n",
                "# Verify AMFI codes\n",
                "valid_amfi = set(fund_master['amfi_code'])\n",
                "nav_history = nav_history[nav_history['amfi_code'].isin(valid_amfi)]\n",
                "print(f\"Verified {len(valid_amfi)} AMFI codes in Fund Master.\")\n",
                "\n",
                "# Validate numeric columns\n",
                "nav_history['nav'] = pd.to_numeric(nav_history['nav'], errors='coerce')\n",
                "nav_history = nav_history.dropna(subset=['nav'])\n",
                "benchmark_indices['close_value'] = pd.to_numeric(benchmark_indices['close_value'], errors='coerce')\n",
                "benchmark_indices = benchmark_indices.dropna(subset=['close_value'])\n",
                "\n",
                "# Sort\n",
                "nav_history = nav_history.sort_values(['amfi_code', 'date']).reset_index(drop=True)\n",
                "benchmark_indices = benchmark_indices.sort_values(['index_name', 'date']).reset_index(drop=True)\n",
                "print(\"Validation and sorting complete.\")"
            ]
        },
        # Step 2: Daily Returns
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Compute Daily Returns\n",
                "We calculate the daily returns for each mutual fund scheme using:\n",
                "$$daily\\_return = \\frac{NAV_t}{NAV_{t-1}} - 1$$\n",
                "We calculate returns separately for each AMFI code, sort by date before calculation, remove the first NaN return, flag extreme outliers ($> \\pm 20\\%$), and print descriptive statistics."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "nav_history['daily_return'] = nav_history.groupby('amfi_code')['nav'].pct_change()\n",
                "nav_history_clean = nav_history.dropna(subset=['daily_return']).copy()\n",
                "\n",
                "# Outliers\n",
                "outliers = nav_history_clean[nav_history_clean['daily_return'].abs() > 0.20]\n",
                "print(f\"Extreme outliers (> ±20% daily return): {len(outliers)}\")\n",
                "\n",
                "# Stats\n",
                "print(\"\\n--- Descriptive Statistics for Daily Returns ---\")\n",
                "stats = {\n",
                "    'Mean': nav_history_clean['daily_return'].mean(),\n",
                "    'Median': nav_history_clean['daily_return'].median(),\n",
                "    'Standard Deviation': nav_history_clean['daily_return'].std(),\n",
                "    'Minimum': nav_history_clean['daily_return'].min(),\n",
                "    'Maximum': nav_history_clean['daily_return'].max(),\n",
                "    'Skewness': skew(nav_history_clean['daily_return']),\n",
                "    'Kurtosis': kurtosis(nav_history_clean['daily_return'])\n",
                "}\n",
                "for k, v in stats.items():\n",
                "    print(f\"{k}: {v:.6f}\")\n",
                "\n",
                "# Save to CSV\n",
                "nav_history_clean.to_csv('../data/processed/returns_computed.csv', index=False)\n",
                "\n",
                "# Plotting\n",
                "plt.figure(figsize=(10, 5))\n",
                "sns.histplot(nav_history_clean['daily_return'], bins=100, kde=True, color='#0F2C59')\n",
                "plt.title('Daily Return Distribution')\n",
                "plt.xlabel('Daily Return')\n",
                "plt.show()"
            ]
        },
        # Step 3: CAGR
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Compute CAGR (1, 3, 5 Years)\n",
                "CAGR (Compound Annual Growth Rate) is computed using:\n",
                "$$CAGR = \\left(\\frac{Ending\\ NAV}{Beginning\\ NAV}\\right)^{\\frac{1}{Number\\ of\\ Years}} - 1$$\n",
                "We handle insufficient history gracefully and ignore incomplete periods. Values are rounded to four decimal places."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "cagr_list = []\n",
                "for code, group in nav_history_clean.groupby('amfi_code'):\n",
                "    group = group.sort_values('date')\n",
                "    ending_date = group['date'].max()\n",
                "    ending_nav = group['nav'].iloc[-1]\n",
                "    \n",
                "    fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]\n",
                "    \n",
                "    def get_cagr_n_years(years):\n",
                "        target_date = ending_date - pd.DateOffset(years=years)\n",
                "        idx = (group['date'] - target_date).abs().idxmin()\n",
                "        row = group.loc[idx]\n",
                "        if abs((row['date'] - target_date).days) > 7:\n",
                "            return np.nan\n",
                "        return (ending_nav / row['nav']) ** (1.0 / years) - 1.0\n",
                "        \n",
                "    cagr_1 = get_cagr_n_years(1)\n",
                "    cagr_3 = get_cagr_n_years(3)\n",
                "    cagr_5 = get_cagr_n_years(5)\n",
                "    \n",
                "    cagr_list.append({\n",
                "        'amfi_code': code,\n",
                "        'scheme_name': fund_info['scheme_name'],\n",
                "        'fund_house': fund_info['fund_house'],\n",
                "        'category': fund_info['category'],\n",
                "        '1-Year CAGR': round(cagr_1, 4) if not np.isnan(cagr_1) else np.nan,\n",
                "        '3-Year CAGR': round(cagr_3, 4) if not np.isnan(cagr_3) else np.nan,\n",
                "        '5-Year CAGR': round(cagr_5, 4) if not np.isnan(cagr_5) else np.nan\n",
                "    })\n",
                "    \n",
                "df_cagr = pd.DataFrame(cagr_list).sort_values('5-Year CAGR', ascending=False, na_position='last')\n",
                "df_cagr.to_csv('../data/processed/cagr_report.csv', index=False)\n",
                "print(\"CAGR Report preview:\")\n",
                "df_cagr.head(10)"
            ]
        },
        # Step 4: Sharpe Ratio
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 4. Compute Sharpe Ratio\n",
                "The Sharpe Ratio measures the excess return per unit of standard deviation (volatility):\n",
                "$$Sharpe = \\frac{R_p - R_f}{\\sigma_p}$$\n",
                "We use a risk-free rate ($R_f$) of $6.5\\%$. Volatility is annualized using daily returns standard deviation $\\times \\sqrt{252}$."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "rf = 0.065\n",
                "sharpe_list = []\n",
                "for code, group in nav_history_clean.groupby('amfi_code'):\n",
                "    returns = group['daily_return'].values\n",
                "    ann_return = np.mean(returns) * 252\n",
                "    ann_vol = np.std(returns) * np.sqrt(252)\n",
                "    sharpe = (ann_return - rf) / ann_vol if ann_vol > 0 else np.nan\n",
                "    \n",
                "    fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]\n",
                "    sharpe_list.append({\n",
                "        'amfi_code': code,\n",
                "        'scheme_name': fund_info['scheme_name'],\n",
                "        'annualized_return': ann_return,\n",
                "        'annualized_volatility': ann_vol,\n",
                "        'sharpe_ratio': sharpe\n",
                "    })\n",
                "    \n",
                "df_sharpe = pd.DataFrame(sharpe_list).sort_values('sharpe_ratio', ascending=False).reset_index(drop=True)\n",
                "df_sharpe['rank'] = df_sharpe['sharpe_ratio'].rank(ascending=False, method='min')\n",
                "df_sharpe.to_csv('../data/processed/sharpe_values.csv', index=False)\n",
                "\n",
                "print(\"Top 5 Sharpe Ratios:\")\n",
                "print(df_sharpe.head(5))\n",
                "print(\"\\nBottom 5 Sharpe Ratios:\")\n",
                "print(df_sharpe.tail(5))\n",
                "\n",
                "# Top 10 Sharpe plot\n",
                "plt.figure(figsize=(10, 5))\n",
                "sns.barplot(x='sharpe_ratio', y='scheme_name', data=df_sharpe.head(10), palette='crest')\n",
                "plt.title('Top 10 Sharpe Ratios')\n",
                "plt.show()"
            ]
        },
        # Step 5: Sortino Ratio
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 5. Compute Sortino Ratio\n",
                "Sortino ratio differs from Sharpe ratio by only considering downside standard deviation:\n",
                "$$Sortino = \\frac{R_p - R_f}{\\sigma_d}$$\n",
                "We use only negative daily return observations to compute downside standard deviation, and annualize it."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "sortino_list = []\n",
                "for code, group in nav_history_clean.groupby('amfi_code'):\n",
                "    returns = group['daily_return'].values\n",
                "    ann_return = np.mean(returns) * 252\n",
                "    neg_returns = returns[returns < 0]\n",
                "    downside_vol = np.std(neg_returns) * np.sqrt(252) if len(neg_returns) > 1 else np.nan\n",
                "    sortino = (ann_return - rf) / downside_vol if downside_vol > 0 else np.nan\n",
                "    \n",
                "    fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]\n",
                "    sortino_list.append({\n",
                "        'amfi_code': code,\n",
                "        'scheme_name': fund_info['scheme_name'],\n",
                "        'downside_volatility': downside_vol,\n",
                "        'sortino_ratio': sortino\n",
                "    })\n",
                "    \n",
                "df_sortino = pd.DataFrame(sortino_list).sort_values('sortino_ratio', ascending=False).reset_index(drop=True)\n",
                "df_sortino.to_csv('../data/processed/sortino_values.csv', index=False)\n",
                "\n",
                "# Comparison Scatter Plot\n",
                "merged = pd.merge(df_sharpe[['amfi_code', 'sharpe_ratio']], df_sortino[['amfi_code', 'sortino_ratio']], on='amfi_code')\n",
                "plt.figure(figsize=(8, 6))\n",
                "sns.scatterplot(x='sharpe_ratio', y='sortino_ratio', data=merged, color='#E28F22', s=80)\n",
                "sns.regplot(x='sharpe_ratio', y='sortino_ratio', data=merged, scatter=False, color='#0F2C59')\n",
                "plt.title('Sortino vs Sharpe Ratio')\n",
                "plt.xlabel('Sharpe Ratio')\n",
                "plt.ylabel('Sortino Ratio')\n",
                "plt.show()"
            ]
        },
        # Step 6: Alpha & Beta
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 6. Compute Alpha and Beta\n",
                "We calculate Alpha and Beta against the Nifty 100 benchmark index using linear regression:\n",
                "$$Fund\\ Return = Alpha + Beta \\times Benchmark\\ Return$$\n",
                "Alpha is annualized: $Annual\\ Alpha = intercept \\times 252$."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "nifty100 = benchmark_indices[benchmark_indices['index_name'] == 'NIFTY100'].copy()\n",
                "nifty100['bench_return'] = nifty100['close_value'].pct_change()\n",
                "nifty100 = nifty100.dropna(subset=['bench_return'])\n",
                "\n",
                "ab_list = []\n",
                "for code, group in nav_history_clean.groupby('amfi_code'):\n",
                "    merged_ret = pd.merge(group[['date', 'daily_return']], nifty100[['date', 'bench_return']], on='date')\n",
                "    if len(merged_ret) < 30:\n",
                "        continue\n",
                "    slope, intercept, r_val, p_val, std_err = linregress(merged_ret['bench_return'], merged_ret['daily_return'])\n",
                "    \n",
                "    fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]\n",
                "    ab_list.append({\n",
                "        'amfi_code': code,\n",
                "        'scheme_name': fund_info['scheme_name'],\n",
                "        'alpha': intercept * 252,\n",
                "        'beta': slope,\n",
                "        'r_value': r_val,\n",
                "        'p_value': p_val,\n",
                "        'standard_error': std_err\n",
                "    })\n",
                "    \n",
                "df_ab = pd.DataFrame(ab_list).sort_values('alpha', ascending=False).reset_index(drop=True)\n",
                "df_ab.to_csv('../data/processed/alpha_beta.csv', index=False)\n",
                "df_ab.head(5)"
            ]
        },
        # Step 7: Maximum Drawdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 7. Compute Maximum Drawdown\n",
                "Drawdown is calculated as:\n",
                "$$Drawdown = \\frac{NAV_t}{Running\\ Max} - 1$$\n",
                "Maximum Drawdown is the lowest value of Drawdown. We also identify peak start dates, trough end dates, recovery dates, and duration."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "dd_list = []\n",
                "for code, group in nav_history_clean.groupby('amfi_code'):\n",
                "    group = group.sort_values('date').reset_index(drop=True)\n",
                "    dates = group['date'].values\n",
                "    navs = group['nav'].values\n",
                "    \n",
                "    running_max = np.maximum.accumulate(navs)\n",
                "    drawdowns = navs / running_max - 1.0\n",
                "    max_dd = np.min(drawdowns)\n",
                "    \n",
                "    if max_dd >= 0:\n",
                "        dd_list.append({\n",
                "            'amfi_code': code, 'scheme_name': group['amfi_code'].iloc[0], 'max_drawdown': 0.0,\n",
                "            'start_date': np.nan, 'end_date': np.nan, 'recovery_date': np.nan, 'duration_days': 0\n",
                "        })\n",
                "        continue\n",
                "        \n",
                "    trough_idx = np.argmin(drawdowns)\n",
                "    trough_date = dates[trough_idx]\n",
                "    peak_val = running_max[trough_idx]\n",
                "    peak_idx = np.where(navs[:trough_idx+1] == peak_val)[0][0]\n",
                "    peak_date = dates[peak_idx]\n",
                "    \n",
                "    recovery_idx_list = np.where((dates > trough_date) & (navs >= peak_val))[0]\n",
                "    if len(recovery_idx_list) > 0:\n",
                "        rec_date = pd.to_datetime(dates[recovery_idx_list[0]]).strftime('%Y-%m-%d')\n",
                "        duration = (pd.to_datetime(rec_date) - pd.to_datetime(peak_date)).days\n",
                "    else:\n",
                "        rec_date = \"Not Recovered\"\n",
                "        duration = (pd.to_datetime(dates[-1]) - pd.to_datetime(peak_date)).days\n",
                "        \n",
                "    fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]\n",
                "    dd_list.append({\n",
                "        'amfi_code': code,\n",
                "        'scheme_name': fund_info['scheme_name'],\n",
                "        'max_drawdown': max_dd,\n",
                "        'start_date': pd.to_datetime(peak_date).strftime('%Y-%m-%d'),\n",
                "        'end_date': pd.to_datetime(trough_date).strftime('%Y-%m-%d'),\n",
                "        'recovery_date': rec_date,\n",
                "        'duration_days': duration\n",
                "    })\n",
                "    \n",
                "df_dd = pd.DataFrame(dd_list).sort_values('max_drawdown').reset_index(drop=True)\n",
                "df_dd.to_csv('../data/processed/max_drawdown.csv', index=False)\n",
                "df_dd.head(5)"
            ]
        },
        # Step 8: Scorecard
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 8. Build Composite Fund Scorecard\n",
                "The composite score (0-100) is built using a weighted ranking:\n",
                "- **30%**: 3-Year CAGR Rank\n",
                "- **25%**: Sharpe Rank\n",
                "- **20%**: Alpha Rank\n",
                "- **15%**: Expense Ratio Rank (inverse)\n",
                "- **10%**: Max Drawdown Rank (inverse)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "df_m = df_cagr[['amfi_code', '3-Year CAGR', 'fund_house', 'category', 'scheme_name']]\n",
                "df_m = pd.merge(df_m, df_sharpe[['amfi_code', 'sharpe_ratio']], on='amfi_code')\n",
                "df_m = pd.merge(df_m, df_ab[['amfi_code', 'alpha']], on='amfi_code')\n",
                "df_m = pd.merge(df_m, df_dd[['amfi_code', 'max_drawdown']], on='amfi_code')\n",
                "df_m = pd.merge(df_m, fund_master[['amfi_code', 'expense_ratio_pct']], on='amfi_code')\n",
                "\n",
                "df_m['rank_return'] = df_m['3-Year CAGR'].rank(pct=True) * 100\n",
                "df_m['rank_sharpe'] = df_m['sharpe_ratio'].rank(pct=True) * 100\n",
                "df_m['rank_alpha'] = df_m['alpha'].rank(pct=True) * 100\n",
                "df_m['rank_expense'] = df_m['expense_ratio_pct'].rank(ascending=False, pct=True) * 100\n",
                "df_m['rank_drawdown'] = df_m['max_drawdown'].rank(pct=True) * 100\n",
                "\n",
                "df_m['composite_score'] = (\n",
                "    0.30 * df_m['rank_return'] +\n",
                "    0.25 * df_m['rank_sharpe'] +\n",
                "    0.20 * df_m['rank_alpha'] +\n",
                "    0.15 * df_m['rank_expense'] +\n",
                "    0.10 * df_m['rank_drawdown']\n",
                ")\n",
                "\n",
                "df_m = df_m.sort_values('composite_score', ascending=False).reset_index(drop=True)\n",
                "df_m['overall_rank'] = df_m['composite_score'].rank(ascending=False, method='min').astype(int)\n",
                "\n",
                "def assign_grade(score):\n",
                "    if score >= 80: return 'A+'\n",
                "    elif score >= 65: return 'A'\n",
                "    elif score >= 50: return 'B'\n",
                "    elif score >= 35: return 'C'\n",
                "    else: return 'D'\n",
                "\n",
                "df_m['performance_grade'] = df_m['composite_score'].apply(assign_grade)\n",
                "df_m.to_csv('../data/processed/fund_scorecard.csv', index=False)\n",
                "df_m[['scheme_name', 'composite_score', 'overall_rank', 'performance_grade']].head(10)"
            ]
        },
        # Step 9: Benchmark Comparison
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 9. Benchmark Comparison\n",
                "We compare the Top 5 highest-scoring funds against **Nifty 50** and **Nifty 100** benchmarks over the latest available 3-year period. Series are normalized to 100 at starting date."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "top_5_codes = df_m['amfi_code'].head(5).values\n",
                "latest_date = nav_history_clean['date'].max()\n",
                "start_date = latest_date - pd.DateOffset(years=3)\n",
                "\n",
                "plt.figure(figsize=(14, 7))\n",
                "for code in top_5_codes:\n",
                "    sub = nav_history_clean[(nav_history_clean['amfi_code'] == code) & (nav_history_clean['date'] >= start_date)].sort_values('date')\n",
                "    name = df_m[df_m['amfi_code'] == code]['scheme_name'].iloc[0]\n",
                "    norm = (sub['nav'] / sub['nav'].iloc[0]) * 100\n",
                "    plt.plot(sub['date'], norm, label=name[:20])\n",
                "    \n",
                "for idx_name in ['NIFTY50', 'NIFTY100']:\n",
                "    sub = benchmark_indices[(benchmark_indices['index_name'] == idx_name) & (benchmark_indices['date'] >= start_date)].sort_values('date')\n",
                "    norm = (sub['close_value'] / sub['close_value'].iloc[0]) * 100\n",
                "    plt.plot(sub['date'], norm, label=idx_name, linewidth=2.5, linestyle='--')\n",
                "    \n",
                "plt.title('3-Year Performance Comparison vs Benchmarks')\n",
                "plt.xlabel('Date')\n",
                "plt.ylabel('Normalized NAV (base 100)')\n",
                "plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')\n",
                "plt.show()"
            ]
        },
        # Step 10: Tracking Error
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 10. Compute Tracking Error\n",
                "Tracking Error measures the standard deviation of active returns against the benchmark:\n",
                "$$Tracking\\ Error = Std(Fund\\ Return - Benchmark\\ Return) \\times \\sqrt{252}$$\n",
                "We calculate tracking error against Nifty 50 and Nifty 100."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "nifty50 = benchmark_indices[benchmark_indices['index_name'] == 'NIFTY50'].copy()\n",
                "nifty50['return'] = nifty50['close_value'].pct_change()\n",
                "nifty50 = nifty50.dropna(subset=['return'])\n",
                "\n",
                "nifty100 = benchmark_indices[benchmark_indices['index_name'] == 'NIFTY100'].copy()\n",
                "nifty100['return'] = nifty100['close_value'].pct_change()\n",
                "nifty100 = nifty100.dropna(subset=['return'])\n",
                "\n",
                "te_list = []\n",
                "for code, group in nav_history_clean.groupby('amfi_code'):\n",
                "    m50 = pd.merge(group[['date', 'daily_return']], nifty50[['date', 'return']], on='date')\n",
                "    m100 = pd.merge(group[['date', 'daily_return']], nifty100[['date', 'return']], on='date')\n",
                "    \n",
                "    te_50 = np.std(m50['daily_return'] - m50['return']) * np.sqrt(252) if len(m50) > 30 else np.nan\n",
                "    te_100 = np.std(m100['daily_return'] - m100['return']) * np.sqrt(252) if len(m100) > 30 else np.nan\n",
                "    \n",
                "    fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]\n",
                "    te_list.append({\n",
                "        'amfi_code': code,\n",
                "        'scheme_name': fund_info['scheme_name'],\n",
                "        'tracking_error_nifty50': te_50,\n",
                "        'tracking_error_nifty100': te_100\n",
                "    })\n",
                "    \n",
                "df_te = pd.DataFrame(te_list).sort_values('tracking_error_nifty100').reset_index(drop=True)\n",
                "df_te.to_csv('../data/processed/tracking_error.csv', index=False)\n",
                "df_te.head(10)"
            ]
        }
    ]
    
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
    print(f"Generated notebook at {notebook_path}")

if __name__ == "__main__":
    generate_notebook()
