import requests
import datetime
import os

# --- CONFIGURATION ---
# REPLACE 'YOUR_USERNAME' WITH YOUR ACTUAL MONKEYTYPE USERNAME
USERNAME = "Axshay_KK" 
API_KEY = os.environ.get("MONKEYTYPE_API_KEY") 
# ---------------------

def get_data():
    if not API_KEY:
        print("Error: Monkeytype API Key is missing.")
        return []
        
    headers = {"Authorization": f"ApeKey {API_KEY}"}
    url = f"https://api.monkeytype.com/users/{USERNAME}/profile"
    
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

    if "data" not in data or "typingStats" not in data["data"]:
        print("Error fetching data. Check Username/API Key.", data)
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
                            # Convert ms to seconds
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
    # Align start date to a Sunday to match standard calendars
    # (Optional tweak: adjust logic if you want exact 365 days vs aligned weeks)
    
    # 3. SVG Configuration
    cell_size = 12
    gap = 3
    # 53 weeks wide, 7 days tall
    width = 53 * (cell_size + gap) + 20
    height = 7 * (cell_size + gap) + 20
    
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg.append('<rect width="100%" height="100%" fill="#323437" rx="8"/>') # Background (Dark Grey)
    
    # Monkeytype Heatmap Colors (Dark -> Yellow/Brand)
    colors = ["#2c2e31", "#005a5a", "#008888", "#00b9b9", "#e2b714"] 
    
    # Draw the grid
    # We go back 52 weeks from this week's Saturday
    # Find the Sunday of 52 weeks ago
    current_weekday = today.weekday() # Mon=0, Sun=6
    # Shift to last Sunday
    last_sunday = today - datetime.timedelta(days=(current_weekday + 1) % 7) 
    start_date = last_sunday - datetime.timedelta(weeks=52)

    for week in range(53):
        for day in range(7):
            # Calculate actual date for this cell
            cell_date = start_date + datetime.timedelta(weeks=week, days=day)
            date_str = cell_date.strftime('%Y-%m-%d')
            
            # Get test count
            count = counts.get(date_str, 0)
            
            # Pick Color
            fill = colors[0]
            if count > 0: fill = colors[1]
            if count > 5: fill = colors[2]
            if count > 15: fill = colors[3]
            if count > 30: fill = colors[4]

            # Don't draw future days
            if cell_date > today:
                continue

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
        print(f"Generated heatmap with {len(ts)} total tests.")
    else:
        print("No data found or error occurred.")
