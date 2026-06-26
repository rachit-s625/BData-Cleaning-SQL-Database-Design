import os
import pandas as pd
import numpy as np
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def build_scorecard(conn, processed_dir):
    logging.info("Building fund scorecard rankings...")
    
    # Load required data
    df_perf = pd.read_sql("SELECT * FROM fact_performance", conn)
    df_fund = pd.read_sql("SELECT amfi_code, risk_category FROM dim_fund", conn)
    
    df = pd.merge(df_perf, df_fund, on="amfi_code")
    
    if df.empty:
        logging.error("No data available to build scorecard!")
        return None
        
    # Standardize rankings (higher return, higher Sharpe, higher Alpha, lower expense, lower drawdown are better)
    df["rank_return"] = df["return_3yr_pct"].rank(pct=True) * 100
    df["rank_sharpe"] = df["sharpe_ratio"].rank(pct=True) * 100
    df["rank_alpha"] = df["alpha"].rank(pct=True) * 100
    
    # Ranks where lower values are better (expense ratio, max drawdown magnitude)
    df["rank_expense"] = df["expense_ratio_pct"].rank(ascending=False, pct=True) * 100
    df["rank_drawdown"] = df["max_drawdown_pct"].rank(pct=True) * 100  # since max drawdown is negative, larger negative values (worse) rank lower, so ascending=True matches "less negative is better"
    
    # Calculate composite score
    df["composite_score"] = (
        0.30 * df["rank_return"] +
        0.25 * df["rank_sharpe"] +
        0.20 * df["rank_alpha"] +
        0.15 * df["rank_expense"] +
        0.10 * df["rank_drawdown"]
    )
    
    df["rank"] = df["composite_score"].rank(ascending=False, method="min")
    
    # Save scorecard
    scorecard_cols = [
        "amfi_code", "scheme_name", "fund_house", "category", "return_3yr_pct", 
        "sharpe_ratio", "alpha", "expense_ratio_pct", "max_drawdown_pct", 
        "risk_category", "composite_score", "rank"
    ]
    df_scorecard = df[scorecard_cols].sort_values("rank")
    df_scorecard.to_csv(os.path.join(processed_dir, "fund_scorecard.csv"), index=False)
    logging.info("Fund scorecard rankings generated successfully.")
    
    # Update SQLite database table fact_performance (adding composite_score and rank columns)
    # Note: SQLite doesn't require modifying columns dynamically since we can create a view or update the table.
    # Let's save it to a separate table `fact_scorecard` in the database.
    try:
        df_scorecard.to_sql("fact_scorecard", conn, if_exists="replace", index=False)
        logging.info("Saved scorecard to database table fact_scorecard")
    except Exception as e:
        logging.error(f"Error saving scorecard to database: {e}")

    return df_scorecard

def recommend_funds(risk_appetite, scorecard_path):
    if not os.path.exists(scorecard_path):
        print("Scorecard file not found! Please run build_scorecard first.")
        return None
        
    df = pd.read_csv(scorecard_path)
    
    # Map risk appetite to SEBI risk categories
    # SEBI Categories: Low, Low to Moderate, Moderate, Moderately High, High, Very High
    if risk_appetite.lower() == "low":
        eligible_risk = ["Low", "Low to Moderate", "Moderate"]
    elif risk_appetite.lower() == "moderate":
        eligible_risk = ["Moderate", "Moderately High"]
    elif risk_appetite.lower() == "high":
        eligible_risk = ["Moderately High", "High", "Very High"]
    else:
        eligible_risk = list(df["risk_category"].unique())
        
    # Filter and recommend top 3 by Sharpe Ratio
    recommendations = df[df["risk_category"].isin(eligible_risk)].sort_values("sharpe_ratio", ascending=False).head(3)
    return recommendations

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(script_dir, "..", "data", "db", "bluestock_mf.db"))
    processed_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "processed"))
    
    conn = sqlite3.connect(db_path)
    build_scorecard(conn, processed_dir)
    conn.close()
    
    # Print sample recommendations
    scorecard_path = os.path.join(processed_dir, "fund_scorecard.csv")
    print("\n--- SAMPLE FUND RECOMMENDATIONS ---")
    for level in ["Low", "Moderate", "High"]:
        print(f"\nRisk Appetite: {level}")
        recs = recommend_funds(level, scorecard_path)
        if recs is not None and not recs.empty:
            for idx, row in recs.iterrows():
                print(f"  {row['rank']}. {row['scheme_name']} (Sharpe: {row['sharpe_ratio']:.2f}, Risk: {row['risk_category']})")
        else:
            print("  No recommendations found.")

if __name__ == "__main__":
    main()
