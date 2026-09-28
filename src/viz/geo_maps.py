import folium

def create_choropleth(geo_df, value_col, output_path):
    print(f'Creating choropleth map saved to {output_path}')
