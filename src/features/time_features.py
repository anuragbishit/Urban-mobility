import pandas as pd

def extract_time_features(df, timestamp_col):
    df = df.copy()
    df['hour'] = df[timestamp_col].dt.hour
    df['weekday'] = df[timestamp_col].dt.weekday
    df['is_weekend'] = df['weekday'].isin([5, 6]).astype(int)
    return df
