
import os
import csv
import time
import requests

API_KEY = os.getenv("PSI_API_KEY")
STRATEGIES = ["mobile", "desktop"]
RETRY_COUNT = 3
DELAY_SECONDS = 5

INPUT_FILES = [
    "urls_part_1.txt",
    "urls_part_2.txt",
]

OUTPUT_FILE = "psi_results_batch_1.csv"

def fetch_psi_data(url, strategy):
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "strategy": strategy,
        "key": API_KEY,
    }

    for attempt in range(RETRY_COUNT):
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            print(f"⚠️ Failed [{url}] [{strategy}] - HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"🔁 Retry {attempt+1}/{RETRY_COUNT} [{url}] [{strategy}] - {e}")
        time.sleep(DELAY_SECONDS)
    return None

def parse_crux_percentile(value):
    return round(value / 1000, 2) if isinstance(value, (int, float)) else ""

def needs_improvement(lcp, cls, inp):
    try:
        return (
            float(lcp) > 2.5 or
            float(cls) > 0.1 or
            float(inp) > 200
        )
    except:
        return False

def extract_metrics(data, url, strategy):
    lh = data.get("lighthouseResult", {})
    audits = lh.get("audits", {})
    categories = lh.get("categories", {})
    crux = data.get("loadingExperience", {}).get("metrics", {})
    overall_status = data.get("loadingExperience", {}).get("overall_category", "N/A")

    lcp_p75 = parse_crux_percentile(crux.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile", ""))
    cls_p75 = crux.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile", "")
    inp_p75 = parse_crux_percentile(crux.get("INTERACTION_TO_NEXT_PAINT_MS", {}).get("percentile", ""))

    improvement = needs_improvement(lcp_p75, cls_p75, inp_p75)

    return {
        "URL": url,
        "Strategy": strategy,
        "Performance Score": categories.get("performance", {}).get("score", 0) * 100,
        "FCP": audits.get("first-contentful-paint", {}).get("displayValue", ""),
        "LCP": audits.get("largest-contentful-paint", {}).get("displayValue", ""),
        "CLS": audits.get("cumulative-layout-shift", {}).get("displayValue", ""),
        "INP": audits.get("interactive", {}).get("displayValue", ""),
        "CrUX LCP (p75)": lcp_p75,
        "CrUX CLS (p75)": cls_p75,
        "CrUX INP (p75)": inp_p75,
        "Core Web Vitals Status": overall_status,
        "Needs Improvement": "✅ Yes" if improvement else "—"
    }

def run_scan():
    all_urls = []
    for file in INPUT_FILES:
        if os.path.exists(file):
            with open(file, "r") as f:
                all_urls += [line.strip() for line in f if line.strip()]
        else:
            print(f"⚠️ File not found: {file}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "URL", "Strategy", "Performance Score", "FCP", "LCP", "CLS", "INP",
            "CrUX LCP (p75)", "CrUX CLS (p75)", "CrUX INP (p75)",
            "Core Web Vitals Status", "Needs Improvement"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for url in all_urls:
            for strategy in STRATEGIES:
                print(f"🔍 Scanning {url} [{strategy}]")
                data = fetch_psi_data(url, strategy)
                if data:
                    row = extract_metrics(data, url, strategy)
                    writer.writerow(row)
                time.sleep(DELAY_SECONDS)

if __name__ == "__main__":
    run_scan()
