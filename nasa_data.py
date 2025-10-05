# nasa_data.py
import random
from datetime import datetime, timedelta

def get_simulated_smap_data():
    """Simulate NASA SMAP soil moisture data (0-100%)"""
    base = 30
    trend = random.randint(-10, 10)
    return max(10, min(90, base + trend))

def get_simulated_ndvi():
    """Simulate NDVI (Normalized Difference Vegetation Index): 0.1 (bare) to 0.9 (lush)"""
    return round(random.uniform(0.3, 0.7), 2)

def get_smap_timeseries(days=30):
    import pandas as pd
    dates = pd.date_range(end=datetime.today(), periods=days)
    moisture = [max(10, min(90, 30 + random.randint(-15, 15))) for _ in range(days)]
    return pd.DataFrame({"date": dates, "moisture": moisture})

def get_nasa_explanation():
    return {
        "SMAP": "Soil Moisture Active Passive satellite monitors global soil moisture every 2-3 days.",
        "MODIS": "Moderate Resolution Imaging Spectroradiometer tracks vegetation health via NDVI.",
        "ECOSTRESS": "Measures plant temperature to detect water stress."
    }