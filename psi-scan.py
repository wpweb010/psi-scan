# psi-scan.py (Updated)

import requests
import csv
import os
import time

API_KEY = os.getenv("PSI_API_KEY")

STRATEGIES = ["mobile", "desktop"]
URL_FILES = ["urls_part_1.txt", "urls_part_2.txt"]

# Extract PSI Data
def fetch_psi_data(url, strategy):
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "strategy": strategy,
        "key": API_KEY,
        "category": ["performance", "accessibility", "best-practices", "seo"]
    }
    try:
        response = requests.get(endpoint, params=params, timeout=60)
        if response.status_code != 200:
            print(f"Failed to fetch data for {url} [{strategy}] - Status code: {response.status_code}")
            return {"url": url, "strategy": strategy, "error_code": response.status_code}
        return parse_psi_data(response.json(), url, strategy)
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url} [{strategy}]: {e}")
        return {"url": url, "strategy": strategy, "error": str(e)}

# Extract Relevant Fields from PSI + CrUX

def parse_psi_data(data, url, strategy):
    result = {
        "url": url,
        "strategy": strategy,
        "cwv_status": data.get("loadingExperience", {}).get("overall_category", "N/A"),
        "performance_score": data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score", 0) * 100,
        "lcp": data.get("lighthouseResult", {}).get("audits", {}).get("largest-contentful-paint", {}).get("displayValue", "N/A"),
        "cls": data.get("lighthouseResult", {}).get("audits", {}).get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
        "tti": data.get("lighthouseResult", {}).get("audits", {}).get("interactive", {}).get("displayValue", "N/A"),
        "fcp": data.get("lighthouseResult", {}).get("audits", {}).get("first-contentful-paint", {}).get("displayValue", "N/A"),
        "tbt": data.get("lighthouseResult", {}).get("audits", {}).get("total-blocking-time", {}).get("displayValue", "N/A")
    }
    return result

# Main Loop

def run_scan():
    for file in URL_FILES:
        if not os.path.exists(file):
            print(f"❌ File not found: {file}")
            continue

        with open(file, "r") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        results = []

        for url in urls:
            for strategy in STRATEGIES:
                data = fetch_psi_data(url, strategy)
                results.append(data)
                time.sleep(2)  # Avoid throttling

        if results:
            output_file = f"psi_results_{file.replace('.txt', '')}.csv"
            with open(output_file, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            print(f"✅ Results saved to {output_file}")
        else:
            print(f"⚠️ No PSI data collected for {file}, no CSV generated.")

if __name__ == "__main__":
    run_scan()
