"""
FarmSense - Complete NASA Agriculture Game
Copy this entire file as app.py and run with: streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import time
import os

# Page configuration
st.set_page_config(
    page_title="Harvest Horizon: The Satellite Steward",
    page_icon="🌾",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #2E7D32;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #558B2F;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 10px 0;
    }
    .stat-big {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
    }
    .recommendation {
        background: #FFF3E0;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #FF9800;
        margin: 10px 0;
    }
    .success-box {
        background: #E8F5E9;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #4CAF50;
    }
    .warning-box {
        background: #FFF3E0;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #FF9800;
    }
    </style>
""", unsafe_allow_html=True)

# NASA Data Fetcher Class
class NASADataFetcher:
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    def __init__(self):
        self.cache = {}
    
    def get_climate_data(self, lat, lon, days=30):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'parameters': 'T2M,PRECTOTCORR,GWETROOT,ALLSKY_SFC_SW_DWN',
            'community': 'AG',
            'longitude': lon,
            'latitude': lat,
            'start': start_date.strftime('%Y%m%d'),
            'end': end_date.strftime('%Y%m%d'),
            'format': 'JSON'
        }
        
        cache_key = f"{lat}_{lon}_{days}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.cache[cache_key] = data
            return data
        except:
            return self._get_sample_data(days)
    
    def _get_sample_data(self, days=30):
        dates = pd.date_range(end=datetime.now(), periods=days)
        return {
            'properties': {
                'parameter': {
                    'T2M': {date.strftime('%Y%m%d'): 20 + i % 10 + np.random.random() * 3 
                            for i, date in enumerate(dates)},
                    'PRECTOTCORR': {date.strftime('%Y%m%d'): 2.5 + (i % 5) + np.random.random() 
                                    for i, date in enumerate(dates)},
                    'GWETROOT': {date.strftime('%Y%m%d'): 0.3 + (i % 3) * 0.1 + np.random.random() * 0.1 
                                 for i, date in enumerate(dates)},
                    'ALLSKY_SFC_SW_DWN': {date.strftime('%Y%m%d'): 5.5 + np.random.random() 
                                          for i, date in enumerate(dates)}
                }
            }
        }

# Game Logic Class
class FarmingSimulator:
    def __init__(self, scenario_data):
        self.scenario = scenario_data
        self.nasa_data = None
        self.decisions = {'irrigation': 50, 'fertilizer': 50}
        
    def load_nasa_data(self, fetcher):
        loc = self.scenario['location']
        self.nasa_data = fetcher.get_climate_data(loc['lat'], loc['lon'])
    
    def analyze_conditions(self):
        if not self.nasa_data:
            return {}
        
        params = self.nasa_data['properties']['parameter']
        temps = list(params['T2M'].values())
        precip = list(params['PRECTOTCORR'].values())
        soil = list(params['GWETROOT'].values())
        
        return {
            'avg_temperature': round(sum(temps) / len(temps), 1),
            'avg_precipitation': round(sum(precip) / len(precip), 2),
            'avg_soil_moisture': round(sum(soil) / len(soil), 2),
            'temp_data': temps[:10],
            'precip_data': precip[:10],
            'soil_data': soil[:10]
        }
    
    def generate_recommendations(self, analysis):
        recs = []
        soil = analysis['avg_soil_moisture']
        precip = analysis['avg_precipitation']
        temp = analysis['avg_temperature']
        
        if soil < 0.3:
            recs.append("⚠️ Low soil moisture detected - consider increasing irrigation")
        if precip < 2.0:
            recs.append("☀️ Low rainfall period - crops may need supplemental water")
        if temp > 30:
            recs.append("🌡️ High temperatures - increase irrigation to compensate")
        if soil > 0.5 and precip > 5:
            recs.append("💧 High moisture levels - reduce irrigation to prevent overwatering")
        if not recs:
            recs.append("✅ Conditions are optimal for current crop")
        
        return recs
    
    def calculate_yield(self, irrigation, fertilizer):
        analysis = self.analyze_conditions()
        base_yield = 100
        
        soil = analysis['avg_soil_moisture']
        optimal = self.scenario['optimal']
        
        # Irrigation scoring
        if soil < 0.3:
            if irrigation >= 50:
                base_yield += 15
            else:
                base_yield -= 30
        elif soil > 0.5:
            if irrigation <= 30:
                base_yield += 20
            else:
                base_yield -= 25
        else:
            irr_diff = abs(irrigation - optimal['irrigation'])
            base_yield += max(0, 20 - irr_diff / 2)
        
        # Fertilizer scoring
        fert_diff = abs(fertilizer - optimal['fertilizer'])
        if fert_diff <= 10:
            base_yield += 25
        elif fert_diff <= 20:
            base_yield += 10
        elif fertilizer > 80:
            base_yield -= 15
        elif fertilizer < 20:
            base_yield -= 20
        
        yield_pct = max(0, min(150, base_yield))
        water_usage = irrigation * 10
        fert_cost = fertilizer * 5
        
        feedback = self._generate_feedback(yield_pct, analysis, irrigation, fertilizer)
        
        return {
            'yield': yield_pct,
            'water_usage': water_usage,
            'fert_cost': fert_cost,
            'feedback': feedback
        }
    
    def _generate_feedback(self, yield_pct, analysis, irr, fert):
        feedback = []
        
        if yield_pct > 120:
            feedback.append("🎉 Outstanding! You mastered NASA data interpretation!")
        elif yield_pct > 100:
            feedback.append("✅ Excellent work! Your decisions were well-informed.")
        elif yield_pct > 85:
            feedback.append("👍 Good job! Some room for optimization.")
        else:
            feedback.append("📚 Review the NASA data more carefully next time.")
        
        feedback.append(f"\nNASA Data Summary:")
        feedback.append(f"• Avg Temperature: {analysis['avg_temperature']}°C")
        feedback.append(f"• Avg Soil Moisture: {analysis['avg_soil_moisture']}")
        feedback.append(f"• Avg Precipitation: {analysis['avg_precipitation']} mm/day")
        
        feedback.append(f"\nYour Decisions:")
        feedback.append(f"• Irrigation: {irr} units")
        feedback.append(f"• Fertilizer: {fert} units")
        
        return "\n".join(feedback)

    # In your FarmingSimulator class (or as a helper function)
    def generate_html_dashboard(self, nasa_data, scenario_name):
        """Generate a local HTML file with NASA visualizations"""
        import plotly.express as px
        import plotly.io as pio

        # Example: Create a soil moisture chart
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=30),
            'moisture': nasa_data.get('moisture_series', [30]*30)
        })
        
        fig = px.line(df, x='date', y='moisture', 
                    title=f"SMAP Soil Moisture – {scenario_name}",
                    labels={'moisture': 'Moisture (%)'})
        
        # Embed chart in HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Harvest Horizon – {scenario_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f0f8f0; padding: 20px; }}
                h1 {{ color: #2e7d32; }}
                .container {{ max-width: 1200px; margin: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛰️ NASA Dashboard: {scenario_name}</h1>
                <p>Real satellite data driving your farming decisions.</p>
                {pio.to_html(fig, include_plotlyjs='cdn', full_html=False)}
                
                <h2>🌱 Scenario Info</h2>
                <p><strong>Crop:</strong> {self.scenario['name']}</p>
                <p><strong>Difficulty:</strong> {self.scenario['difficulty']}</p
            </div>
        </body>
        </html>
        """
        
        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write(html_content)

# Scenarios
SCENARIOS = {
    'wheat_kansas': {
        'name': '🌾 Wheat Farm - Kansas, USA',
        'difficulty': 'Easy',
        'description': 'Moderate climate with variable rainfall. Learn basic soil moisture monitoring.',
        'location': {'lat': 37.5, 'lon': -95.5},
        'optimal': {'irrigation': 45, 'fertilizer': 50}
    },
    'corn_iowa': {
        'name': '🌽 Corn Farm - Iowa, USA',
        'difficulty': 'Medium',
        'description': 'Higher water needs. Balance abundant water with crop requirements.',
        'location': {'lat': 42.0, 'lon': -93.5},
        'optimal': {'irrigation': 60, 'fertilizer': 55}
    },
    'rice_california': {
        'name': '🍚 Rice Farm - California, USA',
        'difficulty': 'Hard',
        'description': 'High water needs in drought-prone region. Conservation is critical!',
        'location': {'lat': 39.0, 'lon': -121.5},
        'optimal': {'irrigation': 80, 'fertilizer': 45}
    }
}

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = 'welcome'
    st.session_state.nasa_fetcher = NASADataFetcher()
    st.session_state.current_scenario = 'wheat_kansas'
    st.session_state.game = None
    st.session_state.results = None

# Header
st.markdown('<p class="main-header">🌾 Harvest Horizon</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Learn Sustainable Farming with NASA Satellite Data</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📖 About Harvest Horizon")
    st.write("""
    Use real NASA satellite data to make smart farming decisions!
    
    **Learn about:**
    - Temperature monitoring
    - Soil moisture analysis
    - Precipitation patterns
    - Sustainable practices
    """)
    
    st.divider()
    
    st.header("🛰️ NASA Data Sources")
    st.write("""
    - **T2M**: Temperature at 2m
    - **PRECTOTCORR**: Precipitation
    - **GWETROOT**: Soil Moisture
    - **ALLSKY_SFC_SW_DWN**: Solar Radiation
    
    *Data: NASA POWER API*
    """)
    
    st.divider()
    
    if st.button("🔄 Restart Game", use_container_width=True):
        st.session_state.game_state = 'welcome'
        st.session_state.game = None
        st.session_state.results = None
        st.rerun()

# Main Game Logic
if st.session_state.game_state == 'welcome':
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="success-box">
        <h3 style="color: green;">🎯 Your Mission</h3>
        <p style="color: green;">You're a farm manager using NASA satellite data to optimize your harvest. 
        Make smart decisions about irrigation and fertilization based on real climate data!</p>
        <p style="color: green;"><strong>Goal:</strong> Maximize yield while conserving resources.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.subheader("Choose Your Farm:")
        
        scenario_choice = st.radio(
            "Select difficulty level:",
            options=list(SCENARIOS.keys()),
            format_func=lambda x: f"{SCENARIOS[x]['name']} - {SCENARIOS[x]['difficulty']}",
            key='scenario_select'
        )
        
        st.info(SCENARIOS[scenario_choice]['description'])
        
        st.write("")
        if st.button("🚀 Start Farming", use_container_width=True, type="primary"):
            st.session_state.current_scenario = scenario_choice
            st.session_state.game = FarmingSimulator(SCENARIOS[scenario_choice])
            
            with st.spinner("Loading NASA satellite data..."):
                st.session_state.game.load_nasa_data(st.session_state.nasa_fetcher)
                time.sleep(1)
            
            st.session_state.game_state = 'playing'
            st.rerun()
            
        elif st.button("🚀 Or Start Multiplayer Board Farming Game", use_container_width=True, type="secondary"):
            st.session_state.current_scenario = scenario_choice
            st.session_state.game = FarmingSimulator(SCENARIOS[scenario_choice])
            
            with st.spinner("Loading NASA satellite data..."):
                st.session_state.game.load_nasa_data(st.session_state.nasa_fetcher)
                
                # ✅ Generate HTML dashboard after loading data
                # st.session_state.game.generate_html_dashboard(
                #     nasa_data=st.session_state.game.nasa_data,
                #     scenario_name=scenario_choice
                # )
                time.sleep(1)
            
            st.session_state.game_state = 'multi-playing'
            st.session_state.show_dashboard = True  # Flag to show HTML
            st.rerun()

# Show HTML dashboard if game is playing and dashboard exists
elif st.session_state.get('game_state') == 'multi-playing' and st.session_state.get('show_dashboard'):
    if os.path.exists("dashboard.html"):
        with open("dashboard.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        st.subheader("🛰️ Harvest Horizon: The Satellite Steward - Multiplayer")
        components.html(html_content, height=1600, scrolling=True)
    else:
        st.warning("Dashboard not yet generated.") 
            
elif st.session_state.game_state == 'playing':   
    
    game = st.session_state.game
    analysis = game.analyze_conditions()
    
    st.markdown("---")
    st.header("🌍 Step 1: Review NASA Satellite Data")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🌡️ Avg Temperature",
            f"{analysis['avg_temperature']}°C",
            help="NASA POWER API - Temperature at 2 meters"
        )
    
    with col2:
        st.metric(
            "🌧️ Avg Precipitation",
            f"{analysis['avg_precipitation']} mm/day",
            help="Recent rainfall amounts"
        )
    
    with col3:
        st.metric(
            "💧 Soil Moisture",
            f"{analysis['avg_soil_moisture']}",
            help="0-1 scale. Optimal: 0.3-0.5"
        )
    
    # Recommendations
    st.markdown("---")
    st.subheader("💡 NASA Data Insights")
    
    recs = game.generate_recommendations(analysis)
    for rec in recs:
        st.markdown(f'<div class="recommendation" style="color: orange;">{rec}</div>', unsafe_allow_html=True)
    
    # Visualization
    with st.expander("📊 View Detailed Data Charts"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Recent Temperature Trend**")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(range(1, 11), analysis['temp_data'], 'r-o', linewidth=2)
            ax.set_xlabel('Days Ago')
            ax.set_ylabel('Temperature (°C)')
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            plt.close()
        
        with col2:
            st.write("**Recent Precipitation**")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.bar(range(1, 11), analysis['precip_data'], color='skyblue')
            ax.set_xlabel('Days Ago')
            ax.set_ylabel('Rainfall (mm)')
            ax.grid(True, alpha=0.3, axis='y')
            st.pyplot(fig)
            plt.close()
    
    # Decision Making
    st.markdown("---")
    st.header("🎮 Step 2: Make Your Farming Decisions")
    
    st.markdown("""
    <div class="warning-box" style="color: orange;">
    <strong>⚠️ Think carefully!</strong> Base your decisions on the NASA data above.
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💧 Irrigation Level")
        irrigation = st.slider(
            "How much water to apply?",
            min_value=0,
            max_value=100,
            value=50,
            help="Consider soil moisture and rainfall patterns"
        )
        st.caption(f"💰 Water usage: ~{irrigation * 10} liters")
        
        if analysis['avg_soil_moisture'] < 0.3:
            st.warning("⚠️ Low soil moisture!")
        elif analysis['avg_soil_moisture'] > 0.5:
            st.info("💧 Soil already moist")
    
    with col2:
        st.subheader("🌱 Fertilizer Amount")
        fertilizer = st.slider(
            "How much fertilizer?",
            min_value=0,
            max_value=100,
            value=50,
            help="Optimal range varies by crop"
        )
        st.caption(f"💰 Cost: ${fertilizer * 5}")
        
        if fertilizer > 70:
            st.warning("⚠️ High fertilizer = runoff risk")
        elif fertilizer < 30:
            st.info("💡 Low fertilizer may limit growth")
    
    st.write("")
    
    if st.button("🌾 Harvest & See Results", use_container_width=True, type="primary"):
        results = game.calculate_yield(irrigation, fertilizer)
        st.session_state.results = results
        st.session_state.game_state = 'results'
        st.rerun()

elif st.session_state.game_state == 'results':
    results = st.session_state.results
    yield_pct = results['yield']
    
    st.markdown("---")
    st.header("📊 Harvest Results")
    
    # Big yield display
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if yield_pct > 120:
            st.success("🎉 Outstanding Performance!")
            st.balloons()
        elif yield_pct > 100:
            st.success("✅ Excellent Work!")
        elif yield_pct > 85:
            st.warning("⚠️ Good, Could Be Better")
        else:
            st.error("❌ Needs Improvement")
        
        st.markdown(f'<div class="metric-card"><div class="stat-big">{yield_pct}%</div><div>Crop Yield</div></div>', 
                    unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Details
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Performance Analysis")
        st.text(results['feedback'])
        
        st.divider()
        
        # Efficiency
        efficiency = yield_pct / max(1, results['water_usage'] / 100)
        st.metric("Water Efficiency", f"{efficiency:.1f}%")
    
    with col2:
        st.subheader("💰 Resource Usage")
        st.write(f"**Water Used:** {results['water_usage']} liters")
        st.write(f"**Fertilizer Cost:** ${results['fert_cost']}")
        
        # Visual yield bar
        fig, ax = plt.subplots(figsize=(8, 2))
        color = '#4CAF50' if yield_pct > 100 else '#FF9800' if yield_pct > 85 else '#F44336'
        ax.barh([0], [yield_pct], color=color, height=0.5)
        ax.barh([0], [150], color='lightgray', alpha=0.3, height=0.5)
        ax.set_xlim(0, 150)
        ax.set_ylim(-0.5, 0.5)
        ax.axis('off')
        ax.text(yield_pct/2, 0, f'{yield_pct}%', ha='center', va='center', 
                fontsize=16, fontweight='bold', color='white')
        st.pyplot(fig)
        plt.close()
    
    # Educational content
    st.markdown("---")
    st.subheader("📚 What You Learned")
    st.markdown("""
    <div class="success-box">
    <p style="color: blue;"><strong>NASA satellite data helps farmers:</strong></p>
    <ul>
        <li style="color: blue;">✅ Monitor soil moisture for optimal irrigation</li>
        <li style="color: blue;">✅ Track temperature and rainfall patterns</li>
        <li style="color: blue;">✅ Make data-driven conservation decisions</li>
        <li style="color: blue;">✅ Improve yields sustainably (15-25% increase possible!)</li>
        <li style="color: blue;">✅ Save water (20-30% reduction with precision agriculture)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Try Again", use_container_width=True, type="primary"):
            st.session_state.game_state = 'playing'
            st.session_state.results = None
            st.rerun()
    
    with col2:
        if st.button("🏠 New Scenario", use_container_width=True):
            st.session_state.game_state = 'welcome'
            st.session_state.game = None
            st.session_state.results = None
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>FarmSense</strong> - NASA Space Apps Challenge 2025</p>
    <p>Data Source: NASA POWER API | Built with Python & Streamlit</p>
    <p>🌾 Empowering sustainable agriculture through space technology 🛰️</p>
</div>
""", unsafe_allow_html=True)