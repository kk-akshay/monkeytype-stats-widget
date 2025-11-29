import requests
import datetime
import os
import sys

# --- CONFIGURATION ---
# Confirmed Correct UID (lowercase l's)
USERNAME = "4vNzgKl0lUPmnuCMFGFtOsGnJnp2"
API_KEY = os.environ.get("MONKEYTYPE_API_KEY") 
# ---------------------

def get_data():
    if not API_KEY:
        print("Error: Monkeytype API Key is missing.")
        return []
        
    headers = {"Authorization": f"ApeKey {API_KEY}"}
    
    # FIX 1: Use the /history endpoint to get raw test timestamps
    url = f"https://api.monkeytype.com/users/{USERNAME}/history?isUid=true"
    
    try:
        print(f"Fetching history for UID: {USERNAME}...")
        r = requests.get(url, headers=headers)
        
        if r.status_code != 200:
            print(f"API Error: {r.status_code}")
            print(f"Response: {r.text}")
            return []

        data = r.json()
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

    if "data" not in data:
        print("Error: No 'data' field in response. History might be empty.", data)
        return []

    # FIX 2: Correct parsing for the history list structure
    # The history endpoint returns a list of test objects directly inside "data"
    timestamps = []
    for entry in data["data"]:
        if "timestamp" in entry:
            timestamps.append(entry["timestamp"] / 1000)
            
    return timestamps

def generate_svg(timestamps):
    # 1. Count tests per day
    counts = {}
    for ts in timestamps:
        date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        counts[date_str] = counts.get(date_str, 0) + 1

    # 2. Setup Grid (Last 365 days)
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
        print(f"SUCCESS: Generated heatmap with {len(ts)} total tests.")
    else:
        print("FAILED: No data found.")
