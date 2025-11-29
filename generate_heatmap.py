import requests
import datetime
import os

# --- CONFIGURATION ---
# PASTE YOUR UID HERE (Example: "605386f9...")
# Do NOT use your username. Use the UID from the bottom of Monkeytype Settings.
USERNAME = "Axshay_KK"
API_KEY = os.environ.get("MONKEYTYPE_API_KEY") 
# ---------------------

def get_data():
    if not API_KEY:
        print("Error: Monkeytype API Key is missing from GitHub Secrets.")
        return []
        
    headers = {"Authorization": f"ApeKey {API_KEY}"}
    # Using the UID endpoint is safer than username
    url = f"https://api.monkeytype.com/users/{USERNAME}/profile"
    
    try:
        print(f"Fetching data for User: {USERNAME}...")
        r = requests.get(url, headers=headers)
        
        # DEBUGGING: Print the status code to see why it fails
        print(f"API Status Code: {r.status_code}")
        
        if r.status_code != 200:
            print("ERROR RESPONSE:", r.text)
            return []

        data = r.json()
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

    if "data" not in data or "typingStats" not in data["data"]:
        print("Error: Data structure invalid. You might have no public stats.", data)
        return []

    timestamps = []
    # Monkeytype stores stats nested: typingStats -> time -> 15 -> [results]
    stats = data["data"]["typingStats"]
    
    for mode in stats: # time, words, quote, etc.
        mode_data = stats[mode]
        if isinstance(mode_data, dict):
            for duration in mode_data:
                results = mode_data[duration]
                if isinstance(results, list):
                    for res in results:
                        if "timestamp" in res:
                            timestamps.append(res["timestamp"] / 1000)
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
