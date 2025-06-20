import os
import csv
import json
import time
import requests

API_KEY = os.getenv('PSI_API_KEY')

STRATEGIES = ['mobile', 'desktop']
URL_BATCHES = ['urls_part_1.txt', 'urls_part_2.txt']  # Add more as needed

OUTPUT_DIR = 'psi_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)


FIELD_NAMES = [
    "URL", "Strategy", "Performance", "LCP", "FID", "CLS", "INP",
    "Field LCP", "Field FID", "Field CLS", "Field INP", "CWV Status", "Status"
]

def fetch_psi_data(url, strategy):
    endpoint = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'
    params = {
        'url': url,
        'strategy': strategy,
        'key': API_KEY,
        'category': 'performance'
    }
    try:
        response = requests.get(endpoint, params=params, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch data for {url} [{strategy}] - Status code: {response.status_code}")
            return {"error": response.status_code}
    except Exception as e:
        print(f"Exception for {url} [{strategy}]: {e}")
        return {"error": str(e)}

def extract_data(url, strategy, data):
    try:
        lighthouse = data.get("lighthouseResult", {})
        audits = lighthouse.get("audits", {})
        loading_exp = data.get("loadingExperience", {}).get("metrics", {})
        origin_exp = data.get("originLoadingExperience", {}).get("metrics", {})
        cwv_status = data.get("loadingExperience", {}).get("overall_category", "N/A")

        return {
            "URL": url,
            "Strategy": strategy,
            "Performance": lighthouse.get("categories", {}).get("performance", {}).get("score", "N/A") * 100 if lighthouse.get("categories", {}).get("performance") else "N/A",
            "LCP": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
            "FID": audits.get("max-potential-fid", {}).get("displayValue", "N/A"),
            "CLS": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
            "INP": audits.get("interactive", {}).get("displayValue", "N/A"),
            "Field LCP": loading_exp.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile", origin_exp.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile", "N/A")),
            "Field FID": loading_exp.get("FIRST_INPUT_DELAY_MS", {}).get("percentile", origin_exp.get("FIRST_INPUT_DELAY_MS", {}).get("percentile", "N/A")),
            "Field CLS": loading_exp.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile", origin_exp.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile", "N/A")),
            "Field INP": loading_exp.get("EXPERIMENTAL_INTERACTION_TO_NEXT_PAINT", {}).get("percentile", origin_exp.get("EXPERIMENTAL_INTERACTION_TO_NEXT_PAINT", {}).get("percentile", "N/A")),
            "CWV Status": cwv_status,
            "Status": "Success"
        }
    except Exception as e:
        print(f"Error parsing data for {url} [{strategy}]: {e}")
        return {
            "URL": url,
            "Strategy": strategy,
            "Performance": "Error",
            "LCP": "",
            "FID": "",
            "CLS": "",
            "INP": "",
            "Field LCP": "",
            "Field FID": "",
            "Field CLS": "",
            "Field INP": "",
            "CWV Status": "",
            "Status": f"Error: {e}"
        }

def run_batch_scan(filename):
    results = []
    with open(filename, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
        for url in urls:
            for strategy in STRATEGIES:
                data = fetch_psi_data(url, strategy)
                if "error" not in data:
                    result = extract_data(url, strategy, data)
                else:
                    result = {
                        "URL": url,
                        "Strategy": strategy,
                        "Performance": "",
                        "LCP": "",
                        "FID": "",
                        "CLS": "",
                        "INP": "",
                        "Field LCP": "",
                        "Field FID": "",
                        "Field CLS": "",
                        "Field INP": "",
                        "CWV Status": "",
                        "Status": f"Failed ({data['error']})"
                    }
                results.append(result)
                time.sleep(1)  # to avoid rate limiting

    out_csv = os.path.join(OUTPUT_DIR, f"psi_results_{filename.replace('.txt','')}.csv")
    with open(out_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(results)

if __name__ == '__main__':
    for batch_file in URL_BATCHES:
        run_batch_scan(batch_file)
