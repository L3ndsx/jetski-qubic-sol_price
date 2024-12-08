import requests
import time
import json
import os
from typing import Optional

# Configuration
DATA_FILE = 'data.json'
SOL_PRICE_URL = 'https://jetski.grafana.net/api/public/dashboards/554eb1bf2d224a9eaaf15d4b98b5f4e4/panels/12/query'
EPOCH_URL = 'https://jetskipoolapi.xyz/api/stats'
UPDATE_INTERVAL = 3600  # Interval in seconds between updates

def get_current_timestamp_ms() -> int:
    """Returns the current timestamp in milliseconds."""
    return int(time.time() * 1000)

def get_sol_price() -> Optional[float]:
    """
    Fetches the current SOL price from the API.
    Returns the price as a float or None in case of failure.
    """
    current_timestamp = get_current_timestamp_ms()
    payload = {
        "intervalMs": 60000,
        "maxDataPoints": 179,
        "timeRange": {
            "from": str(current_timestamp - 1000),
            "to": str(current_timestamp),
            "timezone": "browser"
        }
    }

    try:
        response = requests.post(SOL_PRICE_URL, json=payload)
        response.raise_for_status()
        price_raw = response.json()['results']['A']['frames'][0]['data']['values'][0][0]
        sol_price = float(price_raw.replace('$', ''))
        return sol_price
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"[ERROR] Failed to fetch SOL price: {e}")
        return None

def get_epoch() -> Optional[str]:
    """
    Fetches the current epoch from the API.
    Returns the epoch as a string or None in case of failure.
    """
    try:
        response = requests.get(EPOCH_URL)
        response.raise_for_status()
        epoch = str(response.json()['NetworkStats']['epoch'])
        epoch = 150
        return epoch
    except (requests.RequestException, KeyError) as e:
        print(f"[ERROR] Failed to fetch epoch: {e}")
        return None

def load_data(file_path: str = DATA_FILE) -> dict:
    """Loads data from a JSON file."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Failed to read file {file_path}: {e}")
    return {}

def save_data(data: dict, file_path: str = DATA_FILE):
    """Saves data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"[ERROR] Failed to save to file {file_path}: {e}")

def update_sol_data():
    """
    Fetches the SOL price and epoch, then updates the JSON file
    with the new data.
    """
    print("[INFO] Updating data...")
    sol_price = get_sol_price()
    if sol_price is None:
        print("[WARNING] Could not fetch SOL price.")
        return

    epoch = get_epoch()
    if epoch is None:
        print("[WARNING] Could not fetch epoch.")
        return

    current_timestamp = get_current_timestamp_ms()
    data = load_data()

    # Update or add data for the current epoch
    if epoch in data:
        data[epoch].append({'timestamp': current_timestamp, 'sol_price': sol_price})
    else:
        data[epoch] = [{'timestamp': current_timestamp, 'sol_price': sol_price}]

    save_data(data)
    print(f"[SUCCESS] Data added: epoch {epoch}, SOL price {sol_price}.")

def main():
    """Main loop to update data at regular intervals."""
    print("[INFO] Starting data collection.")
    try:
        while True:
            update_sol_data()
            time.sleep(UPDATE_INTERVAL)
    except KeyboardInterrupt:
        print("\n[INFO] Program stopped by user.")

if __name__ == '__main__':
    main()
