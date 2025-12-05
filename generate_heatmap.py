import requests
import datetime
import os
import sys
import json

# --- CONFIGURATION ---
USERNAME = "Axshay_KK"

# UPDATED: Tries to find your 'APE' key first, so it works with your existing setup
API_KEY = os.environ.get("MONKEYTYPE_APE_KEY") or os.environ.get("MONKEYTYPE_API_KEY")
# ---------------------

def get_data():
    headers = {}
    if API_KEY:
        # Note: Monkeytype usually expects "ApeKey" in the header value
        headers["Authorization"] = f"ApeKey {API_KEY}"
    else:
        print("Warning: No API Key provided. Fetching public data only.")
    
    url = f"https://api.monkeytype.com/users/{USERNAME}/profile"
    
    try:
        print(f"Fetching data for USER: {USERNAME}...")
        r = requests.get(url, headers=headers)
        
        if r.status_code != 200:
            print(f"API Error: {r.status_code}")
            return {}

        data = r.json()
    except Exception as e:
        print(f"Connection Error: {e}")
        return {}

    if "data" not in data or "testActivity" not in data["data"]:
        return {}

    activity = data["data"]["testActivity"]
    tests_by_days = activity.get("testsByDays", [])
    last_day_ts = activity.get("lastDay")
    
    if not tests_by_days or not last_day_ts:
        return {}

    last_day_ts = last_day_ts / 1000 
    counts = {}
    last_day_date = datetime.datetime.fromtimestamp(last_day_ts)
    
    # Process data
    for i, count in enumerate(tests_by_days):
        if count is None: continue
        days_ago = len(tests_by_days) - 1 - i
        date = last_day_date - datetime.timedelta(days=days_ago)
        counts[date.strftime('%Y-%m-%d')] = count
                            
    return counts

def generate_svg(counts):
    today = datetime.datetime.now()
    cell_size = 12
    gap = 3
    
    # --- CUSTOMIZATION: 3 MONTHS & YELLOW THEME ---
    weeks_to_show = 13  # Reduced to ~3 months
    
    # Monkeytype Yellow Theme (Serika Dark style)
    # [Empty, Low, Med, High, Max]
    colors = ["#2c2e31", "#665c27", "#998a2f", "#cca72f", "#e2b714"] 
    background_color = "#323437" # Dark Grey Background
    text_color = "#646669"
    # ---------------------------------------------

    left_padding = 30 
    top_padding = 20  
    legend_padding = 20 
    
    width = weeks_to_show * (cell_size + gap) + left_padding + 20
    height = 7 * (cell_size + gap) + top_padding + legend_padding
    
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="font-family: sans-serif; font-size: 10px;">']
    svg.append(f'<rect width="100%" height="100%" fill="{background_color}" rx="8"/>') 
    
    current_weekday = today.weekday() 
    last_sunday = today - datetime.timedelta(days=(current_weekday + 1) % 7) 
    start_date = last_sunday - datetime.timedelta(weeks=weeks_to_show - 1)

    # Day Labels
    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    for i, label in enumerate(day_labels):
        if label:
            y = top_padding + i * (cell_size + gap) + cell_size - 2
            svg.append(f'<text x="5" y="{y}" fill="{text_color}">{label}</text>')

    # Month Labels & Squares
    last_month_index = -1
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    for week in range(weeks_to_show):
        week_start = start_date + datetime.timedelta(weeks=week)
        month_index = week_start.month - 1
        
        if month_index != last_month_index:
            x = left_padding + week * (cell_size + gap)
            svg.append(f'<text x="{x}" y="{top_padding - 5}" fill="{text_color}">{months[month_index]}</text>')
            last_month_index = month_index

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

            x = left_padding + week * (cell_size + gap)
            y = top_padding + day * (cell_size + gap)
            
            svg.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{fill}" rx="2"><title>{date_str}: {count} tests</title></rect>')

    svg.append('</svg>')
    
    with open("monkeytype-heatmap.svg", "w") as f:
        f.write("\n".join(svg))

if __name__ == "__main__":
    counts = get_data()
    if counts:
        generate_svg(counts)
        print(f"SUCCESS: Generated heatmap with {sum(counts.values())} total tests.")
    else:
        print("FAILED: No data found.")
