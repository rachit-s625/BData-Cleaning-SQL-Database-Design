-- 10 SQL Analytical Queries for Bluestock Mutual Fund Platform

-- 1. Top 5 funds by AUM
SELECT 
    amfi_code, 
    scheme_name, 
    fund_house, 
    category, 
    aum_crore 
FROM fact_performance 
ORDER BY aum_crore DESC 
LIMIT 5;

-- 2. Average NAV per month for HDFC Top 100 (amfi_code 125497)
SELECT 
    amfi_code,
    strftime('%Y-%m', date) AS month, 
    AVG(nav) AS avg_nav 
FROM fact_nav 
WHERE amfi_code = 125497
GROUP BY amfi_code, month 
ORDER BY month;

-- 3. Highest 3-Year CAGR funds
SELECT 
    amfi_code, 
    scheme_name, 
    return_3yr_pct 
FROM fact_performance 
ORDER BY return_3yr_pct DESC 
LIMIT 5;

-- 4. Lowest expense ratio funds
SELECT 
    amfi_code, 
    scheme_name, 
    expense_ratio_pct 
FROM dim_fund 
ORDER BY expense_ratio_pct ASC 
LIMIT 5;

-- 5. SIP YoY growth trend
SELECT 
    month, 
    sip_inflow_crore, 
    yoy_growth_pct 
FROM fact_sip_industry 
ORDER BY month;

-- 6. Investor count by state
SELECT 
    state, 
    COUNT(DISTINCT investor_id) AS investor_count 
FROM fact_transactions 
GROUP BY state 
ORDER BY investor_count DESC;

-- 7. Fund category performance (Average 3-Year Return and Sharpe Ratio)
SELECT 
    category, 
    AVG(return_3yr_pct) AS avg_return_3yr, 
    AVG(sharpe_ratio) AS avg_sharpe 
FROM fact_performance 
GROUP BY category 
ORDER BY avg_return_3yr DESC;

-- 8. Portfolio sector allocation across all funds
SELECT 
    sector, 
    ROUND(SUM(weight_pct), 2) AS total_weight 
FROM fact_portfolio 
GROUP BY sector 
ORDER BY total_weight DESC;

-- 9. Transaction type distribution (count and total amount)
SELECT 
    transaction_type, 
    COUNT(*) AS tx_count, 
    SUM(amount_inr) AS total_amount 
FROM fact_transactions 
GROUP BY transaction_type;

-- 10. Monthly AUM trend for top fund houses
SELECT 
    fund_house, 
    date, 
    aum_crore 
FROM fact_aum 
ORDER BY fund_house, date;
