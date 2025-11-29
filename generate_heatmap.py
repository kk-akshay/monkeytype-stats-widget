import requests
import datetime
import os
import sys
import json

# --- CONFIGURATION ---
# We are using the /results endpoint because it relies on the API KEY.
# This bypasses the Username/UID confusion entirely.
API_KEY = os.environ.get("MONKEYTYPE_API_KEY") 
# ---------------------

def get_data():
    if not API_KEY:
        print("CRITICAL ERROR: Monkeytype API Key is missing from secrets.")
        return []
        
    headers = {"Authorization": f"ApeKey {API_KEY}"}
    
    # We use /results because it gives the detailed history needed for the graph
    # We limit to 1000 tests to ensure we get enough data for the year
    url = "https://api.monkeytype.com/results"
    params = {"limit": 1000}
    
    try:
        print(f"DEBUG: Requesting data from {url}...")
        r = requests.get(url, headers=headers, params=params)
        
        # --- DEBUGGING SECTION ---
        print(f"DEBUG: Status Code: {r.status_code}")
        
        try:
            response_json = r.json()
            # Print the first 200 characters of the response to check structure
            # (Printing the whole thing might be too huge for logs, but we print a summary)
            print("--- RAW MONKEYTYPE RESPONSE START ---")
            print(json.dumps(response_json, indent=2)[:2000]) # Limit to first 2000 chars
            print("... (truncated) ...")
            print("--- RAW MONKEYTYPE RESPONSE END ---")
        except:
            print("DEBUG: Could not parse JSON. Raw Text:", r.text)
            return []
        # -------------------------

        if r.status_code != 200:
            return []

        data = response_json

    except Exception as e:
        print(f"Connection Error: {e}")
        return []

    if "data" not in data:
        print("ERROR: Response does not contain 'data' list.")
        return []
    
    result_list = data["data"]
    
    if not result_list:
        print("DEBUG: The 'data' list is empty. You have 0 tests recorded on this account.")
        return []

    print(f"SUCCESS: Found {len(result_list)} tests.")

    timestamps = []
    for test in result_list:
        # Check for different timestamp keys used by different API versions
        if "timestamp" in test:
            timestamps.append(test["timestamp"] / 1000)
        elif "ts" in test:
            timestamps.append(test["ts"] / 1000)
            
    return timestamps

def generate_svg(timestamps):
    counts = {}
    for ts in timestamps:
        date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        counts[date_str] = counts.get(date_str, 0) + 1

    today = datetime.datetime.now()
    cell_size = 12
    gap = 3
    width = 53 * (cell_size + gap) + 20
    height = 7 * (cell_size + gap) + 20
    
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg.append('<rect width="100%" height="100%" fill="#323437" rx="8"/>') 
    
    colors = ["#2c2e31", "#005a5a", "#008888", "#00b9b9", "#e2b714"] 
    
    current_weekday = today.weekday() 
    last_sunday = today - datetime.timedelta(days=(current_weekday + 1) % 7) 
    start_date = last_sunday - datetime.timedelta(weeks=52)

    for week in range(53):
        for day in range(7):
            cell_date = start_date + datetime.timedelta(weeks=week, days=day)
            date_str = cell_date.strftime('%Y-%m-%d')
            count = counts.get(date_str, 0)
            
            fill = colors[0]
            if count > 0: fill = colors[1]
            if count > 5: fill = colors[2]
            if count > 15: fill = colors[3]
            if count > 30: fill = colors[4]

            if cell_date > today: continue

            x = week * (cell_size + gap) + 10
            y = day * (cell_size + gap) + 10
            svg.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{fill}" rx="2" />')

    svg.append('</svg>')
    
    with open("monkeytype-heatmap.svg", "w") as f:
        f.write("\n".join(svg))

if __name__ == "__main__":
    ts = get_data()
    if ts:
        generate_svg(ts)
        print(f"Heatmap generated successfully with {len(ts)} points.")
    else:
        print("FAILED: No timestamp data found.")
