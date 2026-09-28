import pandas as pd
import numpy as np
import os
import argparse
from datetime import timedelta

def generate_sample_data(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    np.random.seed(42)
    n_records = 5000
    
    # Generate dates over 30 days
    start_date = pd.to_datetime('2024-01-01')
    dates = [start_date + timedelta(hours=int(np.random.normal(loc=12, scale=8)), days=np.random.randint(0, 30)) for _ in range(n_records)]
    
    cities = np.random.choice(['New York', 'San Francisco', 'London'], n_records, p=[0.5, 0.3, 0.2])
    
    # Lat/Lon ranges for cities
    city_coords = {
        'New York': {'lat': 40.7128, 'lon': -74.0060},
        'San Francisco': {'lat': 37.7749, 'lon': -122.4194},
        'London': {'lat': 51.5074, 'lon': -0.1278}
    }
    
    zones = np.random.choice(['Downtown', 'Airport', 'Suburbs'], n_records, p=[0.6, 0.15, 0.25])
    
    lats = [city_coords[c]['lat'] + np.random.normal(0, 0.05) for c in cities]
    lons = [city_coords[c]['lon'] + np.random.normal(0, 0.05) for c in cities]
    
    fares = np.random.gamma(shape=2.0, scale=10.0, size=n_records) + 5.0
    status = np.random.choice(['completed', 'cancelled', 'no_driver'], n_records, p=[0.85, 0.10, 0.05])
    
    trips_df = pd.DataFrame({
        'trip_id': [f'T{i:05d}' for i in range(n_records)],
        'request_time': dates,
        'city': cities,
        'zone': zones,
        'pickup_lat': lats,
        'pickup_lon': lons,
        'fare_amount': fares,
        'status': status
    })
    
    trips_df = trips_df.sort_values('request_time').reset_index(drop=True)
    
    trips_df.to_csv(os.path.join(output_dir, 'trips_sample.csv'), index=False)
    print(f'Sample data generated in {output_dir} with {n_records} records.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate-sample', action='store_true')
    args = parser.parse_args()
    
    if args.generate_sample:
        generate_sample_data(os.path.join(r'c:\Users\ANURAG KUMAR SINGH\Desktop\urban mobility\Urban-Mobility-Ride-Hailing-Analytics', 'data_sample'))
