import os
import requests
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mapping of scheme names to AMFI codes
SCHEMES = {
    "HDFC Top 100": 125497,
    "SBI Bluechip": 119551,
    "ICICI Bluechip": 120503,
    "Nippon Large Cap": 118632,
    "Axis Bluechip": 119092,
    "Kotak Bluechip": 120841
}

def fetch_live_nav(scheme_name, scheme_code, output_dir):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    logging.info(f"Fetching NAV data for {scheme_name} (Code: {scheme_code}) from {url}...")
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data_json = response.json()
        
        if "data" in data_json and data_json["data"]:
            nav_list = data_json["data"]
            # Convert to DataFrame
            df = pd.DataFrame(nav_list)
            # Add scheme code
            df["amfi_code"] = scheme_code
            
            # Reorder columns
            df = df[["amfi_code", "date", "nav"]]
            
            # Save to CSV
            output_file = os.path.join(output_dir, f"live_nav_{scheme_code}.csv")
            df.to_csv(output_file, index=False)
            logging.info(f"Successfully saved {len(df)} rows to {output_file}")
            return df
        else:
            logging.warning(f"No data returned for scheme code {scheme_code}")
            return None
    except Exception as e:
        logging.error(f"Error fetching data for {scheme_name} (Code: {scheme_code}): {e}")
        return None

def main():
    # Base directory setup
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "raw"))
    os.makedirs(output_dir, exist_ok=True)
    
    for name, code in SCHEMES.items():
        fetch_live_nav(name, code, output_dir)

if __name__ == "__main__":
    main()
