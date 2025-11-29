import requests
import datetime
import os
import sys
import json

# --- CONFIGURATION ---
# CRITICAL: We use the Monkeytype USERNAME, not the UID.
# Your screenshots confirm your user is "Axshay_KK"
USERNAME = "Axshay_KK"
API_KEY = os.environ.get("MONKEYTYPE_API_KEY") 
# ---------------------

def get_data():
    if not API_KEY:
        print("Error: Monkeytype API Key is missing.")
        return []
        
    headers = {"Authorization": f"ApeKey {API_KEY}"}
    
    # We switch back to /profile because it contains 'typingStats' with timestamps.
    # We do NOT use ?isUid=true because we are using the username.
    url = f"https://api.monkeytype.com/users/{USERNAME}/profile"
    
    try:
        print(f"Fetching data for USER: {USERNAME}...")
        r = requests.get(url, headers=headers)
        
        if r.status_code != 200:
            print(f"API Error: {r.status_code}")
            print(f"Response: {r.text}")
            return []

        data = r.json()
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

    # Validation
    if "data" not in data:
        print("Error: No data returned.", data)
        return []

    if "typingStats" not in data["data"]:
        print("Error: 'typingStats' missing. Ensure Profile > Privacy > Typing Stats is PUBLIC.", data)
        return []

    timestamps = []
    stats = data["data"]["typingStats"]
    
    # PARSING: Extract timestamps from the profile data
    # This method is safer than /history because it groups data by mode
    for mode in stats:
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
        print(f"SUCCESS: Generated heatmap with {len(ts)} total tests.")
    else:
        print("FAILED: No data found.")
