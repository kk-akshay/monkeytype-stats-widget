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
    headers = {}
    if API_KEY:
        headers["Authorization"] = f"ApeKey {API_KEY}"
    else:
        print("Warning: No API Key provided. Fetching public data only.")
    
    url = f"https://api.monkeytype.com/users/{USERNAME}/profile"
    
    try:
        print(f"Fetching data for USER: {USERNAME}...")
        r = requests.get(url, headers=headers)
        
        if r.status_code != 200:
            print(f"API Error: {r.status_code}")
            print(f"Response: {r.text}")
            return {}

        data = r.json()
    except Exception as e:
        print(f"Connection Error: {e}")
        return {}

    # Validation
    if "data" not in data:
        print("Error: No data returned.", data)
        return {}

    if "testActivity" not in data["data"]:
        print("Error: 'testActivity' missing.", data)
        return {}

    activity = data["data"]["testActivity"]
    if "testsByDays" not in activity or "lastDay" not in activity:
        print("Error: Invalid 'testActivity' structure.", activity)
        return {}

    tests_by_days = activity["testsByDays"]
    last_day_ts = activity["lastDay"] / 1000 # Convert to seconds
    
    # Calculate dates backwards from lastDay
    counts = {}
    last_day_date = datetime.datetime.fromtimestamp(last_day_ts)
    
    for i, count in enumerate(tests_by_days):
        if count is None:
            continue
            
        # testsByDays is ordered from oldest to newest? Or newest to oldest?
        # Usually these arrays are ordered chronologically.
        # Let's assume the last element corresponds to lastDay.
        # Wait, let's verify the structure. 
        # The API response showed a list with many nulls and then a 3 at the end.
        # And lastDay was 1764374400000 (2025-11-29).
        # So the last element is the count for lastDay.
        # And we iterate backwards.
        
        # Actually, let's iterate normally but calculate the date for each index.
        # If the array has N elements, the last one is at index N-1 and corresponds to lastDay.
        # So element at index i corresponds to lastDay - (N - 1 - i) days.
        
        days_ago = len(tests_by_days) - 1 - i
        date = last_day_date - datetime.timedelta(days=days_ago)
        date_str = date.strftime('%Y-%m-%d')
        counts[date_str] = count
                            
    return counts

def generate_svg(counts):
    today = datetime.datetime.now()
    cell_size = 12
    gap = 3
    
    # Layout configuration
    left_padding = 30 # Space for day labels
    top_padding = 20  # Space for month labels
    legend_padding = 20 # Space for legend (future proofing, or just bottom margin)
    
    width = 53 * (cell_size + gap) + left_padding + 20
    height = 7 * (cell_size + gap) + top_padding + legend_padding
    
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="font-family: sans-serif; font-size: 10px;">']
    svg.append(f'<rect width="100%" height="100%" fill="#323437" rx="8"/>') 
    
    colors = ["#2c2e31", "#005a5a", "#008888", "#00b9b9", "#e2b714"] 
    
    current_weekday = today.weekday() 
    last_sunday = today - datetime.timedelta(days=(current_weekday + 1) % 7) 
    start_date = last_sunday - datetime.timedelta(weeks=52)

    # Day Labels (Mon, Wed, Fri)
    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    for i, label in enumerate(day_labels):
        if label:
            y = top_padding + i * (cell_size + gap) + cell_size - 2
            svg.append(f'<text x="5" y="{y}" fill="#646669">{label}</text>')

    # Month Labels
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month_index = -1
    
    for week in range(53):
        # Check for month change
        # We use the first day of the week to decide the month label position
        week_start = start_date + datetime.timedelta(weeks=week)
        month_index = week_start.month - 1
        
        if month_index != last_month_index:
            x = left_padding + week * (cell_size + gap)
            svg.append(f'<text x="{x}" y="{top_padding - 5}" fill="#646669">{months[month_index]}</text>')
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
            
            # Add tooltip title
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
