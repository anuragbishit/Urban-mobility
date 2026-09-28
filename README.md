# Urban Mobility Ride-Hailing Analytics

![Urban Mobility Analytics](https://img.shields.io/badge/Status-Active-brightgreen.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)

## Overview
**Urban Mobility Ride-Hailing Analytics** is an end-to-end data analytics and machine learning pipeline designed to process, analyze, and forecast ride-hailing data within urban environments. It includes an interactive, glassmorphism-themed **Streamlit dashboard** equipped with rich geospatial visualizations (Plotly, PyDeck) to help stakeholders understand mobility patterns, demand, and operational efficiency.

## Key Features
* **ETL Pipelines (`src/etl`)**: Robust data extraction and transformation pipelines capable of handling large datasets (Parquet/CSV) and database integrations.
* **Geospatial Feature Engineering (`src/features`)**: Advanced spatial analysis using H3 hexagons, GeoPandas, and Shapely to map coordinates to regions and calculate distances.
* **Demand Forecasting (`src/models`)**: Machine learning models (LightGBM, Prophet, Baseline models) to predict ride demand based on historical temporal and spatial data.
* **Interactive Dashboard (`app.py`)**: A comprehensive Streamlit web app with dynamic filtering, KPIs, heatmaps, and route visualizations.
* **Containerized Deployment**: Ready-to-deploy Docker and Docker Compose configuration.
* **Continuous Integration**: Automated testing setup via Pytest and GitHub Actions (`.github/`).

## Project Structure
```text
Urban-Mobility-Ride-Hailing-Analytics/
│
├── app.py                 # Main Streamlit dashboard application
├── src/                   # Core source code modules
│   ├── etl/               # Data ingestion and cleaning scripts
│   ├── features/          # Feature engineering (spatial/temporal)
│   ├── models/            # ML models and baseline forecasters
│   ├── utils/             # Helper functions and configurations
│   └── viz/               # Visualization rendering logic
├── tests/                 # Unit tests (pytest)
├── notebooks/             # Jupyter notebooks for EDA and prototyping
├── dashboards/            # External dashboard files (e.g., PowerBI)
├── data_sample/           # Sample datasets for testing/demo
├── sql/                   # Database schema and query scripts
├── outputs/               # Generated reports, models, and figures
├── requirements.txt       # Python package dependencies
├── Dockerfile             # Docker container blueprint
└── docker-compose.yml     # Multi-container orchestration
```

## Tech Stack
* **Core & Data Processing:** Python, Pandas, Numpy, PyArrow
* **Geospatial & Mapping:** GeoPandas, Uber H3, Shapely, PyDeck, Folium, GeoPy
* **Machine Learning:** Scikit-Learn, LightGBM, Prophet, Statsmodels
* **Visualization:** Streamlit, Plotly Express/Graph Objects
* **Infrastructure:** Docker, Pytest, GitHub Actions

## Getting Started

### Prerequisites
Make sure you have Python 3.10 or higher installed. It is recommended to use a virtual environment.

### 1. Installation
Clone the repository and install the required dependencies:

```bash
# Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Unix/MacOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Running the Dashboard
You can launch the interactive Streamlit dashboard locally by running:

```bash
streamlit run app.py
```
The application will open in your default web browser (usually at `http://localhost:8501`).

### 3. Running Tests
To ensure everything is working correctly, run the test suite using `pytest`:

```bash
pytest tests/
```

## Docker Deployment
To run the application inside an isolated Docker container, use Docker Compose:

```bash
docker-compose up --build -d
```
Stop the containers with `docker-compose down`.

## License
Distributed under the MIT License. See `LICENSE` for more information.
