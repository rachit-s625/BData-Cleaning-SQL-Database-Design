import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress, skew, kurtosis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def map_benchmark_name(master_bench):
    if not isinstance(master_bench, str):
        return 'NIFTY100'
    name = master_bench.upper()
    if '100' in name:
        return 'NIFTY100'
    elif '50' in name and 'MIDCAP' not in name:
        return 'NIFTY50'
    elif 'MIDCAP 150' in name or 'MID-CAP' in name or 'MIDCAP' in name:
        return 'NIFTY_MIDCAP150'
    elif 'SMALLCAP' in name or 'SMALL CAP' in name:
        return 'BSE_SMALLCAP'
    elif '500' in name:
        return 'NIFTY500'
    elif 'LIQUID' in name:
        return 'CRISIL_LIQUID'
    elif 'GILT' in name:
        return 'CRISIL_GILT'
    return 'NIFTY100'

def load_and_validate_data():
    logging.info("Step 1: Loading and validating datasets...")
    base_dir = "/Users/rachits/Desktop/bluestock"
    
    # Load raw CSVs
    fund_master = pd.read_csv(os.path.join(base_dir, "01_fund_master.csv"))
    nav_history = pd.read_csv(os.path.join(base_dir, "02_nav_history.csv"))
    scheme_performance = pd.read_csv(os.path.join(base_dir, "07_scheme_performance.csv"))
    benchmark_indices = pd.read_csv(os.path.join(base_dir, "10_benchmark_indices.csv"))
    
    # Validation report dict
    report = {}
    
    # 1. Missing values check
    report['missing_values'] = {
        'fund_master': fund_master.isnull().sum().to_dict(),
        'nav_history': nav_history.isnull().sum().to_dict(),
        'scheme_performance': scheme_performance.isnull().sum().to_dict(),
        'benchmark_indices': benchmark_indices.isnull().sum().to_dict()
    }
    
    # 2. Remove duplicates
    len_before_fm = len(fund_master)
    fund_master = fund_master.drop_duplicates()
    report['duplicates_removed_fund_master'] = len_before_fm - len(fund_master)
    
    len_before_nav = len(nav_history)
    nav_history = nav_history.drop_duplicates()
    report['duplicates_removed_nav_history'] = len_before_nav - len(nav_history)
    
    len_before_sp = len(scheme_performance)
    scheme_performance = scheme_performance.drop_duplicates()
    report['duplicates_removed_scheme_performance'] = len_before_sp - len(scheme_performance)
    
    len_before_bi = len(benchmark_indices)
    benchmark_indices = benchmark_indices.drop_duplicates()
    report['duplicates_removed_benchmark_indices'] = len_before_bi - len(benchmark_indices)
    
    # 3. Convert all dates to datetime
    nav_history['date'] = pd.to_datetime(nav_history['date'])
    benchmark_indices['date'] = pd.to_datetime(benchmark_indices['date'])
    fund_master['launch_date'] = pd.to_datetime(fund_master['launch_date'])
    
    # 4. Verify AMFI codes
    valid_amfi_codes = set(fund_master['amfi_code'])
    nav_history = nav_history[nav_history['amfi_code'].isin(valid_amfi_codes)]
    scheme_performance = scheme_performance[scheme_performance['amfi_code'].isin(valid_amfi_codes)]
    report['valid_amfi_count'] = len(valid_amfi_codes)
    
    # 5. Validate numeric columns
    nav_history['nav'] = pd.to_numeric(nav_history['nav'], errors='coerce')
    nav_history = nav_history.dropna(subset=['nav'])
    benchmark_indices['close_value'] = pd.to_numeric(benchmark_indices['close_value'], errors='coerce')
    benchmark_indices = benchmark_indices.dropna(subset=['close_value'])
    
    # 6. Sort by AMFI code and date
    nav_history = nav_history.sort_values(by=['amfi_code', 'date']).reset_index(drop=True)
    benchmark_indices = benchmark_indices.sort_values(by=['index_name', 'date']).reset_index(drop=True)
    
    # 7. Alignment of benchmark and NAV dates
    report['nav_date_min'] = nav_history['date'].min().strftime('%Y-%m-%d')
    report['nav_date_max'] = nav_history['date'].max().strftime('%Y-%m-%d')
    report['bench_date_min'] = benchmark_indices['date'].min().strftime('%Y-%m-%d')
    report['bench_date_max'] = benchmark_indices['date'].max().strftime('%Y-%m-%d')
    
    logging.info("Validation complete.")
    for k, v in report.items():
        if k != 'missing_values':
            logging.info(f"  {k}: {v}")
            
    return fund_master, nav_history, scheme_performance, benchmark_indices, report

def compute_daily_returns(nav_history):
    logging.info("Step 2: Computing daily returns...")
    nav_history['daily_return'] = nav_history.groupby('amfi_code')['nav'].pct_change()
    
    # Remove first NaN returns
    nav_history_clean = nav_history.dropna(subset=['daily_return']).copy()
    
    # Flag extreme outliers (> +/- 20%)
    outliers = nav_history_clean[nav_history_clean['daily_return'].abs() > 0.20]
    logging.info(f"Flagged {len(outliers)} extreme outliers (> ±20% daily return).")
    if len(outliers) > 0:
        logging.warning(outliers[['amfi_code', 'date', 'nav', 'daily_return']])
        
    # Calculate descriptive stats across all daily returns
    stats = {
        'Mean': nav_history_clean['daily_return'].mean(),
        'Median': nav_history_clean['daily_return'].median(),
        'Standard Deviation': nav_history_clean['daily_return'].std(),
        'Minimum': nav_history_clean['daily_return'].min(),
        'Maximum': nav_history_clean['daily_return'].max(),
        'Skewness': skew(nav_history_clean['daily_return']),
        'Kurtosis': kurtosis(nav_history_clean['daily_return'])
    }
    
    logging.info("Descriptive Statistics for daily returns:")
    for k, v in stats.items():
        logging.info(f"  {k}: {v:.6f}")
        
    # Save daily returns
    output_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/data/processed"
    os.makedirs(output_dir, exist_ok=True)
    nav_history_clean.to_csv(os.path.join(output_dir, "returns_computed.csv"), index=False)
    
    return nav_history_clean, stats

def compute_cagr(nav_history, fund_master):
    logging.info("Step 3: Computing CAGR (1-Yr, 3-Yr, 5-Yr)...")
    
    cagr_list = []
    
    for code, group in nav_history.groupby('amfi_code'):
        group = group.sort_values('date')
        ending_date = group['date'].max()
        ending_nav = group['nav'].iloc[-1]
        
        fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]
        fund_name = fund_info['scheme_name']
        fund_house = fund_info['fund_house']
        category = fund_info['category']
        
        cagr_1 = np.nan
        cagr_3 = np.nan
        cagr_5 = np.nan
        
        # Helper to compute CAGR for N years
        def get_cagr_n_years(years):
            target_date = ending_date - pd.DateOffset(years=years)
            # Find closest date
            idx = (group['date'] - target_date).abs().idxmin()
            closest_row = group.loc[idx]
            if abs((closest_row['date'] - target_date).days) > 7:
                return np.nan
            start_nav = closest_row['nav']
            return (ending_nav / start_nav) ** (1.0 / years) - 1.0
            
        cagr_1 = get_cagr_n_years(1)
        cagr_3 = get_cagr_n_years(3)
        cagr_5 = get_cagr_n_years(5)
        
        cagr_list.append({
            'amfi_code': code,
            'scheme_name': fund_name,
            'fund_house': fund_house,
            'category': category,
            '1-Year CAGR': round(cagr_1, 4) if not np.isnan(cagr_1) else np.nan,
            '3-Year CAGR': round(cagr_3, 4) if not np.isnan(cagr_3) else np.nan,
            '5-Year CAGR': round(cagr_5, 4) if not np.isnan(cagr_5) else np.nan
        })
        
    df_cagr = pd.DataFrame(cagr_list)
    df_cagr = df_cagr.sort_values(by='5-Year CAGR', ascending=False, na_position='last')
    
    output_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/data/processed"
    df_cagr.to_csv(os.path.join(output_dir, "cagr_report.csv"), index=False)
    
    return df_cagr

def compute_sharpe(nav_history, fund_master):
    logging.info("Step 4: Computing Sharpe Ratio...")
    
    rf = 0.065
    sharpe_list = []
    
    for code, group in nav_history.groupby('amfi_code'):
        fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]
        fund_name = fund_info['scheme_name']
        
        returns = group['daily_return'].values
        if len(returns) < 30:
            continue
            
        ann_return = np.mean(returns) * 252
        ann_volatility = np.std(returns) * np.sqrt(252)
        
        sharpe = (ann_return - rf) / ann_volatility if ann_volatility > 0 else np.nan
        
        sharpe_list.append({
            'amfi_code': code,
            'scheme_name': fund_name,
            'annualized_return': ann_return,
            'annualized_volatility': ann_volatility,
            'sharpe_ratio': sharpe
        })
        
    df_sharpe = pd.DataFrame(sharpe_list)
    df_sharpe = df_sharpe.sort_values(by='sharpe_ratio', ascending=False)
    df_sharpe['rank'] = df_sharpe['sharpe_ratio'].rank(ascending=False, method='min')
    
    output_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/data/processed"
    df_sharpe.to_csv(os.path.join(output_dir, "sharpe_values.csv"), index=False)
    
    return df_sharpe

def compute_sortino(nav_history, fund_master):
    logging.info("Step 5: Computing Sortino Ratio...")
    
    rf = 0.065
    sortino_list = []
    
    for code, group in nav_history.groupby('amfi_code'):
        fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]
        fund_name = fund_info['scheme_name']
        
        returns = group['daily_return'].values
        if len(returns) < 30:
            continue
            
        ann_return = np.mean(returns) * 252
        
        # Sortino downside deviation: std of ONLY negative daily return observations
        neg_returns = returns[returns < 0]
        if len(neg_returns) > 1:
            downside_vol = np.std(neg_returns) * np.sqrt(252)
            sortino = (ann_return - rf) / downside_vol if downside_vol > 0 else np.nan
        else:
            downside_vol = np.nan
            sortino = np.nan
            
        sortino_list.append({
            'amfi_code': code,
            'scheme_name': fund_name,
            'downside_volatility': downside_vol,
            'sortino_ratio': sortino
        })
        
    df_sortino = pd.DataFrame(sortino_list)
    df_sortino = df_sortino.sort_values(by='sortino_ratio', ascending=False)
    df_sortino['rank'] = df_sortino['sortino_ratio'].rank(ascending=False, method='min')
    
    output_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/data/processed"
    df_sortino.to_csv(os.path.join(output_dir, "sortino_values.csv"), index=False)
    
    return df_sortino

def compute_alpha_beta(nav_history, benchmark_indices, fund_master):
    logging.info("Step 6: Computing Alpha and Beta against Nifty 100...")
    
    # Calculate Nifty 100 daily returns
    nifty100 = benchmark_indices[benchmark_indices['index_name'] == 'NIFTY100'].copy()
    nifty100 = nifty100.sort_values('date')
    nifty100['bench_return'] = nifty100['close_value'].pct_change()
    nifty100 = nifty100.dropna(subset=['bench_return'])
    
    ab_list = []
    
    for code, group in nav_history.groupby('amfi_code'):
        fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]
        fund_name = fund_info['scheme_name']
        
        # Merge returns on date
        merged = pd.merge(group[['date', 'daily_return']], nifty100[['date', 'bench_return']], on='date')
        if len(merged) < 30:
            continue
            
        # Linear regression
        slope, intercept, r_value, p_value, std_err = linregress(merged['bench_return'], merged['daily_return'])
        
        beta = slope
        alpha_daily = intercept
        alpha_ann = alpha_daily * 252
        
        ab_list.append({
            'amfi_code': code,
            'scheme_name': fund_name,
            'alpha': alpha_ann,
            'beta': beta,
            'r_value': r_value,
            'p_value': p_value,
            'standard_error': std_err
        })
        
    df_ab = pd.DataFrame(ab_list)
    df_ab = df_ab.sort_values(by='alpha', ascending=False)
    
    output_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/data/processed"
    df_ab.to_csv(os.path.join(output_dir, "alpha_beta.csv"), index=False)
    
    return df_ab

def compute_max_drawdown(nav_history, fund_master):
    logging.info("Step 7: Computing Maximum Drawdown...")
    
    dd_list = []
    
    for code, group in nav_history.groupby('amfi_code'):
        group = group.sort_values('date').reset_index(drop=True)
        dates = group['date'].values
        navs = group['nav'].values
        
        fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]
        fund_name = fund_info['scheme_name']
        
        running_max = np.maximum.accumulate(navs)
        drawdowns = navs / running_max - 1.0
        max_dd = np.min(drawdowns)
        
        if max_dd >= 0:
            dd_list.append({
                'amfi_code': code,
                'scheme_name': fund_name,
                'max_drawdown': 0.0,
                'start_date': np.nan,
                'end_date': np.nan,
                'recovery_date': np.nan,
                'duration_days': 0
            })
            continue
            
        trough_idx = np.argmin(drawdowns)
        trough_date = dates[trough_idx]
        
        # Peak value before trough
        peak_val = running_max[trough_idx]
        # Peak index
        peak_idx = np.where(navs[:trough_idx+1] == peak_val)[0][0]
        peak_date = dates[peak_idx]
        
        # Recovery date: first index after trough where NAV >= peak_val
        recovery_idx_list = np.where((dates > trough_date) & (navs >= peak_val))[0]
        if len(recovery_idx_list) > 0:
            recovery_idx = recovery_idx_list[0]
            recovery_date = dates[recovery_idx]
            # Duration in days
            duration = (pd.to_datetime(recovery_date) - pd.to_datetime(peak_date)).days
            recovery_date_str = pd.to_datetime(recovery_date).strftime('%Y-%m-%d')
        else:
            recovery_date_str = "Not Recovered"
            duration = (pd.to_datetime(dates[-1]) - pd.to_datetime(peak_date)).days
            
        dd_list.append({
            'amfi_code': code,
            'scheme_name': fund_name,
            'max_drawdown': max_dd,
            'start_date': pd.to_datetime(peak_date).strftime('%Y-%m-%d'),
            'end_date': pd.to_datetime(trough_date).strftime('%Y-%m-%d'),
            'recovery_date': recovery_date_str,
            'duration_days': duration
        })
        
    df_dd = pd.DataFrame(dd_list)
    df_dd = df_dd.sort_values(by='max_drawdown') # largest negative first
    
    output_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/data/processed"
    df_dd.to_csv(os.path.join(output_dir, "max_drawdown.csv"), index=False)
    
    return df_dd

def build_scorecard(df_cagr, df_sharpe, df_alpha_beta, df_drawdown, fund_master):
    logging.info("Step 8: Building Composite Fund Scorecard...")
    
    # Merge all metrics
    # 3-Year CAGR
    df_temp1 = df_cagr[['amfi_code', '3-Year CAGR', 'fund_house', 'category', 'scheme_name']]
    df_temp2 = pd.merge(df_temp1, df_sharpe[['amfi_code', 'sharpe_ratio']], on='amfi_code')
    df_temp3 = pd.merge(df_temp2, df_alpha_beta[['amfi_code', 'alpha']], on='amfi_code')
    df_temp4 = pd.merge(df_temp3, df_drawdown[['amfi_code', 'max_drawdown']], on='amfi_code')
    
    # Join with expense ratio from fund_master
    df_score = pd.merge(df_temp4, fund_master[['amfi_code', 'expense_ratio_pct']], on='amfi_code')
    
    # Ranks (Higher rank_score is better)
    df_score['rank_return'] = df_score['3-Year CAGR'].rank(pct=True) * 100
    df_score['rank_sharpe'] = df_score['sharpe_ratio'].rank(pct=True) * 100
    df_score['rank_alpha'] = df_score['alpha'].rank(pct=True) * 100
    
    # Lower expense is better, so rank descending
    df_score['rank_expense'] = df_score['expense_ratio_pct'].rank(ascending=False, pct=True) * 100
    # Less negative drawdown is better, so rank ascending (since -5% > -25%)
    df_score['rank_drawdown'] = df_score['max_drawdown'].rank(pct=True) * 100
    
    # Compute composite score
    df_score['composite_score'] = (
        0.30 * df_score['rank_return'] +
        0.25 * df_score['rank_sharpe'] +
        0.20 * df_score['rank_alpha'] +
        0.15 * df_score['rank_expense'] +
        0.10 * df_score['rank_drawdown']
    )
    
    df_score = df_score.sort_values(by='composite_score', ascending=False).reset_index(drop=True)
    df_score['overall_rank'] = df_score['composite_score'].rank(ascending=False, method='min').astype(int)
    
    # Grade mapping
    def assign_grade(score):
        if score >= 80: return 'A+'
        elif score >= 65: return 'A'
        elif score >= 50: return 'B'
        elif score >= 35: return 'C'
        else: return 'D'
        
    df_score['performance_grade'] = df_score['composite_score'].apply(assign_grade)
    
    output_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/data/processed"
    df_score.to_csv(os.path.join(output_dir, "fund_scorecard.csv"), index=False)
    
    return df_score

def compute_tracking_error(nav_history, benchmark_indices, fund_master):
    logging.info("Step 10: Computing Tracking Error...")
    
    # Calculate benchmark daily returns
    bench_returns = {}
    for idx_name in ['NIFTY50', 'NIFTY100']:
        sub = benchmark_indices[benchmark_indices['index_name'] == idx_name].copy()
        sub = sub.sort_values('date')
        sub['return'] = sub['close_value'].pct_change()
        bench_returns[idx_name] = sub.dropna(subset=['return'])
        
    te_list = []
    
    for code, group in nav_history.groupby('amfi_code'):
        fund_info = fund_master[fund_master['amfi_code'] == code].iloc[0]
        fund_name = fund_info['scheme_name']
        
        # TE vs Nifty 50
        merged50 = pd.merge(group[['date', 'daily_return']], bench_returns['NIFTY50'][['date', 'return']], on='date')
        te_50 = np.std(merged50['daily_return'] - merged50['return']) * np.sqrt(252) if len(merged50) > 30 else np.nan
        
        # TE vs Nifty 100
        merged100 = pd.merge(group[['date', 'daily_return']], bench_returns['NIFTY100'][['date', 'return']], on='date')
        te_100 = np.std(merged100['daily_return'] - merged100['return']) * np.sqrt(252) if len(merged100) > 30 else np.nan
        
        te_list.append({
            'amfi_code': code,
            'scheme_name': fund_name,
            'tracking_error_nifty50': te_50,
            'tracking_error_nifty100': te_100
        })
        
    df_te = pd.DataFrame(te_list)
    df_te = df_te.sort_values(by='tracking_error_nifty100', ascending=True) # Lowest TE first (best tracker)
    
    output_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/data/processed"
    df_te.to_csv(os.path.join(output_dir, "tracking_error.csv"), index=False)
    
    return df_te

def generate_visualizations(nav_history, df_scorecard, df_sharpe, df_sortino, df_alpha_beta, df_drawdown, df_cagr, df_te, benchmark_indices):
    logging.info("Step 11: Generating Visualizations...")
    
    charts_dir = "/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/reports/charts"
    os.makedirs(charts_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")
    
    # 1. Daily Return Distribution
    plt.figure(figsize=(12, 6))
    sns.histplot(nav_history['daily_return'], bins=100, kde=True, color='#0F2C59')
    plt.title('Daily Return Distribution (All Funds)')
    plt.xlabel('Daily Return')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "daily_return_distribution.png"), dpi=300)
    plt.close()
    
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='category', y='daily_return', data=pd.merge(nav_history, df_scorecard[['amfi_code', 'category']], on='amfi_code'), palette='viridis')
    plt.title('Daily Return Distribution by Category')
    plt.xlabel('Category')
    plt.ylabel('Daily Return')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "daily_return_boxplot.png"), dpi=300)
    plt.close()
    
    # 2. NAV Growth Comparison (top 5 vs bottom 5 schemes based on Scorecard)
    plt.figure(figsize=(14, 7))
    top_5_codes = df_scorecard['amfi_code'].head(5).values
    for code in top_5_codes:
        sub = nav_history[nav_history['amfi_code'] == code].sort_values('date')
        name = df_scorecard[df_scorecard['amfi_code'] == code]['scheme_name'].iloc[0]
        # Normalize to 100
        normalized_nav = (sub['nav'] / sub['nav'].iloc[0]) * 100
        plt.plot(sub['date'], normalized_nav, label=name[:30])
    plt.title('NAV Growth Comparison (Top 5 Scoring Funds, Normalized to 100)')
    plt.xlabel('Date')
    plt.ylabel('Normalized NAV')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "nav_growth_comparison.png"), dpi=300)
    plt.close()
    
    # 3. CAGR Comparison (Top 10 Funds)
    plt.figure(figsize=(12, 6))
    top_cagr = df_cagr.dropna(subset=['3-Year CAGR']).head(10)
    sns.barplot(x='3-Year CAGR', y='scheme_name', data=top_cagr, palette='Blues_r')
    plt.title('Top 10 Funds by 3-Year CAGR')
    plt.xlabel('3-Year CAGR (decimal)')
    plt.ylabel('Scheme Name')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "cagr_comparison.png"), dpi=300)
    plt.close()
    
    # 4. Sharpe Ratio Ranking (Top 10 vs Bottom 10)
    plt.figure(figsize=(12, 6))
    top_sharpe = df_sharpe.head(10)
    sns.barplot(x='sharpe_ratio', y='scheme_name', data=top_sharpe, palette='crest')
    plt.title('Top 10 Sharpe Ratios')
    plt.xlabel('Sharpe Ratio')
    plt.ylabel('Scheme Name')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "sharpe_ratio_ranking.png"), dpi=300)
    plt.close()
    
    # 5. Sortino Ratio vs Sharpe Ratio Scatter Plot
    plt.figure(figsize=(10, 8))
    merged_ratios = pd.merge(df_sharpe[['amfi_code', 'sharpe_ratio']], df_sortino[['amfi_code', 'sortino_ratio']], on='amfi_code')
    sns.scatterplot(x='sharpe_ratio', y='sortino_ratio', data=merged_ratios, color='#E28F22', s=100)
    # add a trendline
    sns.regplot(x='sharpe_ratio', y='sortino_ratio', data=merged_ratios, scatter=False, color='#0F2C59')
    plt.title('Sortino Ratio vs Sharpe Ratio')
    plt.xlabel('Sharpe Ratio')
    plt.ylabel('Sortino Ratio')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "sortino_vs_sharpe_scatter.png"), dpi=300)
    plt.close()
    
    # 6. Alpha & Beta Distributions
    plt.figure(figsize=(12, 6))
    sns.histplot(df_alpha_beta['alpha'], bins=20, kde=True, color='teal')
    plt.title('Alpha Distribution (relative to Nifty 100)')
    plt.xlabel('Annualized Alpha')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "alpha_distribution.png"), dpi=300)
    plt.close()
    
    plt.figure(figsize=(12, 6))
    sns.histplot(df_alpha_beta['beta'], bins=20, kde=True, color='purple')
    plt.title('Beta Distribution (relative to Nifty 100)')
    plt.xlabel('Beta')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "beta_distribution.png"), dpi=300)
    plt.close()
    
    # 7. Maximum Drawdown Comparison (Top 10 lowest drawdowns / safest)
    plt.figure(figsize=(12, 6))
    top_dd = df_drawdown.sort_values(by='max_drawdown', ascending=False).head(10) # least negative first
    sns.barplot(x='max_drawdown', y='scheme_name', data=top_dd, palette='rocket')
    plt.title('Top 10 Funds with Lowest Max Drawdown (Safest)')
    plt.xlabel('Max Drawdown')
    plt.ylabel('Scheme Name')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "max_drawdown_comparison.png"), dpi=300)
    plt.close()
    
    # 8. Scorecard Leaderboard (Top 20 horizontal bar chart)
    plt.figure(figsize=(12, 8))
    sns.barplot(x='composite_score', y='scheme_name', data=df_scorecard.head(20), palette='magma')
    plt.title('Top 20 Funds Leaderboard (Composite Score)')
    plt.xlabel('Composite Score')
    plt.ylabel('Scheme Name')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "fund_scorecard_ranking.png"), dpi=300)
    plt.close()
    
    # 9. Tracking Error Ranking (Lowest Nifty 100 TE)
    plt.figure(figsize=(12, 6))
    top_te = df_te.head(10)
    sns.barplot(x='tracking_error_nifty100', y='scheme_name', data=top_te, palette='viridis')
    plt.title('Top 10 Funds by Lowest Tracking Error vs Nifty 100')
    plt.xlabel('Tracking Error')
    plt.ylabel('Scheme Name')
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, "tracking_error_ranking.png"), dpi=300)
    plt.close()
    
    # 10. Benchmark Comparison (Top 5 funds vs Nifty 50 and Nifty 100)
    # latest 3 years period
    latest_date = nav_history['date'].max()
    start_date = latest_date - pd.DateOffset(years=3)
    
    plt.figure(figsize=(14, 7))
    for code in top_5_codes:
        sub = nav_history[(nav_history['amfi_code'] == code) & (nav_history['date'] >= start_date)].sort_values('date')
        name = df_scorecard[df_scorecard['amfi_code'] == code]['scheme_name'].iloc[0]
        norm = (sub['nav'] / sub['nav'].iloc[0]) * 100
        plt.plot(sub['date'], norm, label=name[:20], alpha=0.7)
        
    # Add Nifty 50 and Nifty 100
    for idx_name in ['NIFTY50', 'NIFTY100']:
        sub = benchmark_indices[(benchmark_indices['index_name'] == idx_name) & (benchmark_indices['date'] >= start_date)].sort_values('date')
        norm = (sub['close_value'] / sub['close_value'].iloc[0]) * 100
        plt.plot(sub['date'], norm, label=idx_name, linewidth=2.5, linestyle='--')
        
    plt.title('3-Year Performance Comparison: Top 5 Scoring Funds vs Benchmarks (Normalized to 100)')
    plt.xlabel('Date')
    plt.ylabel('Normalized NAV / Value')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join("/Users/rachits/Desktop/bluestock/bluestock_mf_capstone/reports", "benchmark_comparison.png"), dpi=300)
    plt.close()
    
    logging.info("All plots saved successfully.")

def main():
    fund_master, nav_history, scheme_perf, bench, report = load_and_validate_data()
    nav_history_clean, stats = compute_daily_returns(nav_history)
    df_cagr = compute_cagr(nav_history_clean, fund_master)
    df_sharpe = compute_sharpe(nav_history_clean, fund_master)
    df_sortino = compute_sortino(nav_history_clean, fund_master)
    df_alpha_beta = compute_alpha_beta(nav_history_clean, bench, fund_master)
    df_drawdown = compute_max_drawdown(nav_history_clean, fund_master)
    df_scorecard = build_scorecard(df_cagr, df_sharpe, df_alpha_beta, df_drawdown, fund_master)
    df_te = compute_tracking_error(nav_history_clean, bench, fund_master)
    
    generate_visualizations(nav_history_clean, df_scorecard, df_sharpe, df_sortino, df_alpha_beta, df_drawdown, df_cagr, df_te, bench)
    logging.info("Performance Analytics script run complete.")

if __name__ == "__main__":
    main()
