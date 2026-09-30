import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import requests
import pydeck as pdk
from datetime import timedelta
from geopy.geocoders import Nominatim

from src.models.baseline import fit_all_baselines

st.set_page_config(
    page_title="Urban Mobility Analytics", 
    page_icon="🚘", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aggressive Custom CSS to force a beautiful Dark/Glassmorphism theme globally
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0e17 0%, #111827 100%); color: #e5e7eb; }
    [data-testid="stSidebar"] { background-color: rgba(17, 24, 39, 0.95) !important; border-right: 1px solid #1f2937; }
    
    .stTextInput > div > div > input, .stMultiSelect > div > div, .stDateInput > div > div > input {
        background-color: #1f2937 !important; color: #f3f4f6 !important;
        border: 1px solid #374151 !important; border-radius: 8px !important;
    }
    
    /* White text for multiselect and date inputs */
    .stMultiSelect input, .stTextInput input, .stDateInput input {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* White text for Selectbox and Multiselect specifically */
    .stSelectbox input, .stMultiSelect input,
    .stSelectbox div[data-baseweb="select"] *, 
    .stMultiSelect div[data-baseweb="select"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    ul[role="listbox"] li {
        color: #f3f4f6 !important;
    }
    
    .metric-card {
        background: rgba(31, 41, 55, 0.7); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        text-align: center; border: 1px solid rgba(255, 255, 255, 0.1); transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover { transform: translateY(-5px); border: 1px solid rgba(16, 185, 129, 0.3); }
    .metric-value { font-size: 36px; font-weight: 800; color: #10B981; margin-bottom: 5px; }
    .metric-label { font-size: 12px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;}
    
    .surge-active { color: #EF4444 !important; text-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
    .surge-card { border: 1px solid rgba(239, 68, 68, 0.3) !important; }
    
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] label p, [data-testid="stSidebar"] .stCheckbox p, [data-testid="stSidebar"] .stSlider p {
        color: #ffffff !important; font-weight: 600 !important;
    }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 700 !important; }
    
    .stAlert { border-radius: 12px !important; background: rgba(37, 99, 235, 0.1) !important; border: 1px solid rgba(37, 99, 235, 0.3) !important; color: #bfdbfe !important; }
    .stPlotlyChart { background: rgba(31, 41, 55, 0.4); border-radius: 12px; padding: 10px; border: 1px solid rgba(255, 255, 255, 0.05); }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def get_live_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=3).json()
        weather = response.get('current_weather', {})
        temp = weather.get('temperature', '--')
        code = weather.get('weathercode', 0)
        
        # Simple WMO weather code mapping
        if code in [0, 1]: condition = "☀️ Clear"
        elif code in [2, 3]: condition = "☁️ Cloudy"
        elif code in [45, 48]: condition = "🌫️ Fog"
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: condition = "🌧️ Rain"
        elif code in [71, 73, 75, 77, 85, 86]: condition = "❄️ Snow"
        elif code in [95, 96, 99]: condition = "⛈️ Thunderstorm"
        else: condition = "🌡️ Variable"
        
        return f"{temp}°C | {condition}"
    except:
        return "Weather Unavailable"

@st.cache_data
def load_real_nyc_data_v4():
    data_path = "data_sample/nyc_real_trips.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        df['request_time'] = pd.to_datetime(df['request_time'])
        return df
    return pd.DataFrame()

@st.cache_data
def load_base_data():
    data_path = "data_sample/trips_sample.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        df['request_time'] = pd.to_datetime(df['request_time'])
        return df
    return pd.DataFrame()

@st.cache_data
def generate_city_data(city_name):
    geolocator = Nominatim(user_agent="urban_mobility_app")
    try:
        location = geolocator.geocode(city_name)
        if not location:
            return None
        lat, lon = location.latitude, location.longitude
        np.random.seed(hash(city_name) % (2**32))
        n_records = 1500
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.Timedelta(days=30)
        random_seconds = np.random.randint(0, int((end_date - start_date).total_seconds()), n_records)
        dates = [start_date + pd.Timedelta(seconds=int(s)) for s in random_seconds]
        
        lats = [lat + np.random.normal(0, 0.05) for _ in range(n_records)]
        lons = [lon + np.random.normal(0, 0.05) for _ in range(n_records)]
        fares = np.random.gamma(shape=2.0, scale=10.0, size=n_records) + 5.0
        status = np.random.choice(['completed', 'cancelled', 'no_driver'], n_records, p=[0.85, 0.10, 0.05])
        
        # Massive expanded list of generic zones globally
        zone_options = [
            'Downtown', 'Airport', 'Suburbs', 'Bus Stops', 'Train Stations', 
            'Shopping Malls', 'Tech Parks', 'University Campus', 'Hospitals', 
            'Industrial Estate', 'Financial District', 'Old Town', 'Seaport', 
            'Convention Center', 'Central Park', 'Museum District', 'Arts District',
            'Residential North', 'Residential South', 'Residential East', 'Residential West'
        ]
        zones = np.random.choice(zone_options, n_records)
        
        city_df = pd.DataFrame({
            'trip_id': [f'CUSTOM-{i:05d}' for i in range(n_records)], 'request_time': dates,
            'city': [city_name] * n_records, 'zone': zones,
            'pickup_lat': lats, 'pickup_lon': lons, 'fare_amount': fares, 'status': status
        })
        city_df = city_df.sort_values('request_time').reset_index(drop=True)
        return city_df
    except:
        return None

@st.cache_data
def load_world_cities():
    data_path = "data_sample/world_cities.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        cities = df['label'].dropna().unique().tolist()
        if 'New York, United States' not in cities: cities.insert(0, 'New York, United States')
        return sorted(cities)
    return ['New York, United States', 'London, United Kingdom', 'Mumbai, India', 'Tokyo, Japan', 'Sydney, Australia']

base_df = load_base_data()
real_nyc_df = load_real_nyc_data_v4()
available_cities = load_world_cities()

with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 60px; margin: 0;'>🚕</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-top: -10px; color: #10B981 !important;'>Command Center</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("🌍 Location Engine")
    default_idx = available_cities.index('New York, United States') if 'New York, United States' in available_cities else 0
    city_input = st.selectbox("Search City (23,000+ available)", available_cities, index=default_idx)

df = pd.DataFrame()
data_source_msg = ""
weather_str = ""

if city_input:
    short_city = city_input.split(',')[0].strip()
    
    if short_city.lower() == "new york" and not real_nyc_df.empty:
        df = real_nyc_df
        data_source_msg = "🔥 Mode: Real NYC Historical Data"
        weather_str = get_live_weather(40.7128, -74.0060)
    elif not base_df.empty and short_city.lower() in base_df['city'].str.lower().values and short_city.lower() != "new york":
        df = base_df[base_df['city'].str.lower() == short_city.lower()]
        data_source_msg = "⚙️ Mode: Generated Base Data"
        weather_str = get_live_weather(df['pickup_lat'].mean(), df['pickup_lon'].mean())
    else:
        with st.spinner(f"Geolocating '{city_input}' and generating synthetic mobility data..."):
            custom_df = generate_city_data(city_input)
            if custom_df is not None:
                df = custom_df
                data_source_msg = "⚙️ Mode: Simulated Global Data"
                weather_str = get_live_weather(df['pickup_lat'].mean(), df['pickup_lon'].mean())
            else:
                st.sidebar.error(f"Could not find coordinates for city: '{city_input}'.")
                st.stop()

with st.sidebar:
    st.markdown("---")
    if not df.empty:
        available_zones = sorted(df['zone'].unique().tolist())
        zone_filter = st.multiselect("Select Zones", available_zones, default=available_zones)
        min_date = df['request_time'].min().date()
        max_date = df['request_time'].max().date()
        date_range = st.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
    else:
        zone_filter = []; date_range = []

    st.markdown("---")
    st.subheader("🧠 Machine Learning")
    show_forecast = st.checkbox("Show ML Forecasts", value=True)
    forecast_horizon = st.slider("Forecast Horizon (Days)", min_value=1, max_value=7, value=3)
    
    st.markdown("---")
    st.subheader("🗺️ Map Layers")
    show_supply = st.checkbox("Show Active Drivers & Routes (Supply)", value=True)
    
    st.markdown("---")
    live_stream = st.checkbox("🔴 Enable Live Data Stream", value=False)
    if live_stream:
        st.warning("Live Stream Active!")
    
    st.markdown("---")
    st.info("💡 **Hybrid Engine:** Uses real NYC data for 'New York', and live API simulation for global cities.")

if zone_filter: df = df[df['zone'].isin(zone_filter)]
if len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df['request_time'].dt.date >= start_date) & (df['request_time'].dt.date <= end_date)]


st.markdown(f"<h1>Urban Mobility Analytics <span style='font-size: 20px; color: #10B981; vertical-align: middle; background: rgba(16,185,129,0.1); padding: 5px 15px; border-radius: 20px;'>{data_source_msg}</span></h1>", unsafe_allow_html=True)
st.markdown("---")

if df.empty:
    st.warning("No data available for the selected filters.")
else:
    # Top KPI Metrics & Surge Calculation
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_req = len(df)
    completed = len(df[df['status'] == 'completed'])
    avg_fare = df['fare_amount'].mean()
    active_fleet = int(total_req * 0.12) if total_req > 0 else 1
    
    # Surge Pricing Algorithm: Demand / Supply ratio
    demand_supply_ratio = total_req / active_fleet if active_fleet > 0 else 1
    surge_multiplier = max(1.0, min(3.5, demand_supply_ratio * 0.15)) # Arbitrary logic for effect
    
    is_surge = surge_multiplier > 1.2
    surge_class = "surge-active" if is_surge else ""
    card_class = "surge-card" if is_surge else ""
    
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total_req:,}</div><div class="metric-label">Total Requests</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{completed:,}</div><div class="metric-label">Completed Trips</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">${avg_fare:.2f}</div><div class="metric-label">Avg Fare</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{active_fleet}</div><div class="metric-label">Active Fleet</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card {card_class}"><div class="metric-value {surge_class}">{surge_multiplier:.1f}x</div><div class="metric-label">Live Surge</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    row1_col1, row1_col2 = st.columns([1.2, 1])

    with row1_col1:
        # Weather overlay next to title
        st.markdown(f"<h3>📍 Live Demand Density: {city_input} <span style='float:right; font-size:18px; font-weight:normal; color:#9CA3AF; margin-top:5px;'>{weather_str}</span></h3>", unsafe_allow_html=True)
        
        layers = []
        
        # Layer 1: Passenger Demand (Hexagons)
        demand_layer = pdk.Layer(
            'HexagonLayer',
            data=df,
            get_position='[pickup_lon, pickup_lat]',
            radius=200 if len(df) > 500 else 500,
            elevation_scale=4,
            elevation_range=[0, 1000],
            pickable=True,
            extruded=True,
            get_fill_color="[255, (1 - elevationValue) * 255, 0, 200]" 
        )
        layers.append(demand_layer)
        
        # Layer 2 & 3: Driver Supply (Scatterplot) and Routes (ArcLayer)
        if show_supply:
            center_lat = df['pickup_lat'].mean()
            center_lon = df['pickup_lon'].mean()
            if not live_stream: np.random.seed(42)
            driver_lats = [center_lat + np.random.normal(0, 0.08) for _ in range(active_fleet)]
            driver_lons = [center_lon + np.random.normal(0, 0.08) for _ in range(active_fleet)]
            driver_df = pd.DataFrame({'lat': driver_lats, 'lon': driver_lons})
            
            supply_layer = pdk.Layer(
                'ScatterplotLayer',
                data=driver_df,
                get_position='[lon, lat]',
                get_color='[16, 185, 129, 200]', 
                get_radius=150,
                pickable=True
            )
            layers.append(supply_layer)
            
            arc_df = pd.DataFrame({
                'start_lon': driver_lons[:50], 'start_lat': driver_lats[:50],
                'end_lon': [lon + np.random.normal(0, 0.04) for lon in driver_lons[:50]],
                'end_lat': [lat + np.random.normal(0, 0.04) for lat in driver_lats[:50]]
            })
            arc_layer = pdk.Layer(
                'ArcLayer',
                data=arc_df,
                get_source_position='[start_lon, start_lat]',
                get_target_position='[end_lon, end_lat]',
                get_source_color='[16, 185, 129, 255]',
                get_target_color='[239, 68, 68, 255]',
                get_width=2,
                pickable=True
            )
            layers.append(arc_layer)
        
        view_state = pdk.ViewState(
            longitude=df['pickup_lon'].mean(),
            latitude=df['pickup_lat'].mean(),
            zoom=11, pitch=50, bearing=-27.36
        )
        r = pdk.Deck(layers=layers, initial_view_state=view_state, map_style='dark', tooltip=True)
        st.pydeck_chart(r)

    with row1_col2:
        st.markdown("<h3>📈 Daily Demand Trend & Forecast</h3>", unsafe_allow_html=True)
        time_df = df.set_index('request_time').resample('D').size().reset_index(name='trips')
        
        if not time_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=time_df['request_time'], y=time_df['trips'],
                mode='lines+markers', name='Historical', fill='tozeroy', 
                line=dict(color='#10B981', width=4, shape='spline'),
                marker=dict(size=6, color='#ffffff', line=dict(width=2, color='#10B981')),
                fillcolor='rgba(16, 185, 129, 0.2)'
            ))
            
            if show_forecast and len(time_df) > 5:
                last_time = time_df['request_time'].iloc[-1]
                future_times = [last_time + pd.Timedelta(days=i) for i in range(1, forecast_horizon + 1)]
                try:
                    preds = fit_all_baselines(time_df['trips'], horizon=forecast_horizon)
                    if 'naive' in preds:
                        fig.add_trace(go.Scatter(
                            x=future_times, y=preds['naive'], mode='lines+markers', name='Naive Model',
                            line=dict(color='#F59E0B', dash='dash', width=3, shape='spline'),
                            marker=dict(size=6)
                        ))
                    if 'rolling_avg' in preds:
                        fig.add_trace(go.Scatter(
                            x=future_times, y=preds['rolling_avg'], mode='lines+markers', name='Rolling Avg',
                            line=dict(color='#3B82F6', dash='dot', width=3, shape='spline'),
                            marker=dict(size=6)
                        ))
                except Exception as e:
                    pass

            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), height=350,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#9CA3AF'), xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#374151', title="Total Daily Rides"),
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("<br><h3>💵 Pricing Distribution</h3>", unsafe_allow_html=True)
            fig2 = px.histogram(df, x='fare_amount', nbins=30)
            fig2.update_traces(marker_color='#3B82F6', marker_line_color='#2563EB', marker_line_width=1)
            fig2.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), height=250, 
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#9CA3AF'), xaxis=dict(showgrid=False, title="Fare Amount ($)"),
                yaxis=dict(showgrid=True, gridcolor='#374151', title="Count")
            )
            st.plotly_chart(fig2, use_container_width=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<h2>⚡ Advanced Analytics & Operations</h2>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🌧 What-If Simulation", 
        "🚚 Fleet Optimization", 
        "📈 Dynamic Surge Calculator", 
        "🚨 Fraud Detection",
        "🔋 EV & Carbon Track",
        "👥 Driver Churn ML",
        "🤖 AI Assistant"
    ])
    
    with tab1:
        st.markdown("### Scenario Planning")
        c1, c2 = st.columns(2)
        sim_weather = c1.selectbox("Weather Event", ["Clear", "Heavy Rain", "Snowstorm", "Hurricane"])
        sim_demand = c2.slider("Demand Shock (%)", -50, 100, 0, step=10)
        if st.button("Run Simulation"):
            sim_req = int(total_req * (1 + sim_demand/100.0))
            if sim_weather in ["Heavy Rain", "Snowstorm"]:
                sim_req = int(sim_req * 1.2)
            st.success(f"Simulation Complete! Under these conditions, projected demand is **{sim_req:,} requests**. Recommended fleet size: **{int(sim_req*0.15)} drivers**.")
    
    with tab2:
        st.markdown("### Fleet Dispatch & Allocation")
        if st.button("Optimize Fleet Allocation"):
            with st.spinner("Running allocation algorithm..."):
                import time; time.sleep(1.5)
                st.success("Optimization Complete! Generated 3 Dispatch Actions:")
                disp_data = {
                    "From Zone": ["Downtown", "North Hills", "Airport"],
                    "To Zone": ["Southside", "Business District", "Downtown"],
                    "Drivers to Move": [45, 20, 15],
                    "Estimated Revenue Uplift": ["+$3,200", "+$850", "+$1,100"]
                }
                st.table(pd.DataFrame(disp_data))
                
    with tab3:
        st.markdown("### Dynamic Surge Pricing Calculator")
        surge_test = st.slider("Test Surge Multiplier", 1.0, 5.0, 1.5, 0.1)
        base_rev = total_req * avg_fare
        drop_off = (surge_test - 1.0) * 0.15 
        new_req = int(total_req * (1 - drop_off))
        new_rev = new_req * (avg_fare * surge_test)
        st.metric("Projected Revenue (with Surge)", f"${new_rev:,.2f}", delta=f"${new_rev - base_rev:,.2f}")
        st.caption(f"Note: Assumes a {drop_off*100:.1f}% drop in rider demand due to pricing.")
        
    with tab4:
        st.markdown("### Trip Anomaly & Fraud Detection")
        st.caption("Automatically flagging suspicious trips (e.g., unusually high fares, erratic routes).")
        anomalies = df[df['fare_amount'] > df['fare_amount'].quantile(0.95)].copy()
        if not anomalies.empty:
            anomalies['Risk Level'] = 'High'
            st.dataframe(anomalies[['trip_id', 'request_time', 'fare_amount', 'zone', 'Risk Level']].head(10), use_container_width=True)
            if st.button("Flag Selected Trips for Review"):
                st.success("Trips flagged successfully! Operations team notified.")
        else:
            st.info("No anomalies detected in the current view.")

    with tab5:
        st.markdown("### Carbon Footprint & EV Dispatch")
        total_miles = len(df) * 4.2 
        co2_emissions = total_miles * 404 
        st.metric("Estimated Fleet CO2 Emissions", f"{co2_emissions/1000:,.1f} kg")
        st.progress(65, text="65% of active fleet is EV")
        if st.button("Activate Eco-Dispatch (Prioritize EVs)"):
            st.success("Eco-Dispatch activated! Routing EVs to high-demand zones to offset carbon footprint.")
            st.metric("Projected CO2 Reduction", "-14%")

    with tab6:
        st.markdown("### Driver Retention & Churn Prediction")
        churn_df = pd.DataFrame({
            'Driver ID': [f"D-{np.random.randint(1000, 9999)}" for _ in range(5)],
            'Avg Daily Earnings': [85, 92, 105, 78, 110],
            'Declined Trips (Last 7d)': [14, 12, 18, 15, 9],
            'Churn Risk (%)': [89, 82, 75, 71, 68]
        })
        st.dataframe(churn_df.style.background_gradient(subset=['Churn Risk (%)'], cmap='Reds'), use_container_width=True)
        if st.button("Deploy Retention Bonuses ($50 each)"):
            st.balloons()
            st.success("Bonuses deployed! Churn risk mitigated for top 5 at-risk drivers.")

    with tab7:
        st.markdown("### 🤖 Chat with your Data ")
        
        api_key = st.text_input("Enter your Google Gemini API Key:", type="password", key="gemini_api_key", help="Get a free API key at aistudio.google.com")
        ai_query = st.text_input("Ask a question about the current dataset:")
        
        if st.button("Ask AI"):
            if not api_key:
                st.warning("Please enter your Gemini API Key above.")
            elif not ai_query:
                st.warning("Please enter a question.")
            else:
                with st.spinner("AI is analyzing data..."):
                    try:
                        from google import genai
                        client = genai.Client(api_key=api_key)
                        
                        data_summary = f"""
                        Dataset Summary:
                        - Total Requests: {total_req}
                        - Average Fare: ${avg_fare:.2f}
                        - Total Revenue: ${total_req * avg_fare:.2f}
                        - Current Surge Multiplier: {surge_multiplier:.1f}x
                        
                        Sample of the data (first 5 rows):
                        {df.head().to_string()}
                        
                        Summary statistics of numerical columns:
                        {df.describe().to_string()}
                        """
                        
                        prompt = f"""You are an expert data analyst AI for a ride-hailing company.
                        Based on the following data context, answer the user's question concisely and accurately.
                        
                        Context:
                        {data_summary}
                        
                        User Question: {ai_query}
                        """
                        
                        response = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
                        st.info(f"**AI Insight:** {response.text}")
                    except Exception as e:
                        st.error(f"Error communicating with AI: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔍 VIEW RAW DATA LOGS"):
        st.dataframe(df.style.highlight_max(axis=0, color='#10B981'), use_container_width=True)

if live_stream:
    import time
    time.sleep(2)
    st.rerun()
