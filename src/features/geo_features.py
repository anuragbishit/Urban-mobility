import h3

def add_h3_index(df, lat_col, lon_col, res=9):
    def get_hex(row):
        try:
            return h3.geo_to_h3(row[lat_col], row[lon_col], res)
        except:
            return None
    df['h3_index'] = df.apply(get_hex, axis=1)
    return df
