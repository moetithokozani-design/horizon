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
import json

# Page configuration
st.set_page_config(
    page_title="Harvest Horizon: The Satellite Steward",
    page_icon="🌾",
    layout="wide"
)

# Simple, clean CSS that won't break existing layout
st.markdown("""
    <style>
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem !important;
        }
        .sub-header {
            font-size: 1.1rem !important;
        }
        /* Make buttons full width on mobile */
        .stButton button {
            width: 100%;
        }
        /* Stack columns on mobile */
        [data-testid="column"] {
            min-width: 100% !important;
        }
    }
    
    /* Ensure content doesn't get too small */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Basic responsive text */
    .responsive-text {
        font-size: 1rem;
    }
    
    @media (max-width: 480px) {
        .responsive-text {
            font-size: 0.9rem;
        }
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

    def generate_html_dashboard(self, scenario_name):
        """Generate the complete HTML game dashboard with proper responsive design"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Harvest Horizon: The Satellite Steward</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }}

                body {{
                    background: linear-gradient(135deg, #1a3c27 0%, #2d5e3f 100%);
                    color: #fff;
                    min-height: 100vh;
                    padding: 20px;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}

                header {{
                    text-align: center;
                    padding: 20px 0;
                    margin-bottom: 20px;
                }}

                h1 {{
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                    background: linear-gradient(to right, #8bc34a, #4caf50, #2e7d32);
                    -webkit-background-clip: text;
                    background-clip: text;
                    color: transparent;
                }}

                .game-area {{
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                    align-items: center;
                }}

                .game-board {{
                    width: 100%;
                    max-width: 600px;
                    aspect-ratio: 1;
                    background: #1e4620;
                    border-radius: 10px;
                    border: 3px solid #8bc34a;
                    display: grid;
                    grid-template-columns: repeat(11, 1fr);
                    grid-template-rows: repeat(11, 1fr);
                    gap: 2px;
                    padding: 5px;
                }}

                .board-cell {{
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.7rem;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    cursor: pointer;
                }}

                .cell-problem {{ background: rgba(255, 87, 34, 0.4) !important; }}
                .cell-opportunity {{ background: rgba(76, 175, 80, 0.4) !important; }}
                .cell-asset {{ background: rgba(255, 193, 7, 0.4) !important; }}
                .cell-nasa {{ background: rgba(33, 150, 243, 0.4) !important; }}
                .cell-market {{ background: rgba(156, 39, 176, 0.4) !important; }}
                .cell-quiz {{ background: rgba(0, 188, 212, 0.4) !important; }}

                .dice-container {{
                    display: flex;
                    gap: 15px;
                    align-items: center;
                    background: rgba(0, 0, 0, 0.4);
                    padding: 15px 25px;
                    border-radius: 50px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}

                .dice {{
                    width: 60px;
                    height: 60px;
                    background: white;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.8rem;
                    font-weight: bold;
                    color: #333;
                }}

                .roll-btn {{
                    padding: 14px 30px;
                    background: linear-gradient(to right, #ff9800, #ff5722);
                    color: white;
                    border: none;
                    border-radius: 30px;
                    font-size: 1.1rem;
                    font-weight: bold;
                    cursor: pointer;
                }}

                /* Mobile responsiveness */
                @media (max-width: 768px) {{
                    .container {{
                        padding: 10px;
                    }}
                    
                    h1 {{
                        font-size: 2rem;
                    }}
                    
                    .game-board {{
                        max-width: 100%;
                        font-size: 0.6rem;
                    }}
                    
                    .dice {{
                        width: 50px;
                        height: 50px;
                        font-size: 1.5rem;
                    }}
                    
                    .roll-btn {{
                        padding: 12px 25px;
                        font-size: 1rem;
                    }}
                }}

                @media (max-width: 480px) {{
                    h1 {{
                        font-size: 1.8rem;
                    }}
                    
                    .game-board {{
                        font-size: 0.5rem;
                    }}
                    
                    .dice-container {{
                        padding: 12px 20px;
                    }}
                    
                    .dice {{
                        width: 45px;
                        height: 45px;
                        font-size: 1.3rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Harvest Horizon: The Satellite Steward</h1>
                    <p style="color: #c8e6c9;">Roll the dice, manage your farm with NASA data!</p>
                </header>

                <div class="game-area">
                    <div class="game-board" id="game-board">
                        <!-- Board cells will be generated by JavaScript -->
                    </div>

                    <div class="dice-container">
                        <div class="dice" id="dice">1</div>
                        <button class="roll-btn" onclick="rollDice()">Roll Dice</button>
                    </div>
                </div>
            </div>

            <script>
                function initializeBoard() {{
                    const gameBoard = document.getElementById('game-board');
                    const boardSize = 11;
                    const totalCells = boardSize * boardSize;
                    const cellTypes = ['problem', 'opportunity', 'asset', 'nasa-data', 'market', 'quiz'];
                    
                    for (let i = 0; i < totalCells; i++) {{
                        const cell = document.createElement('div');
                        cell.className = 'board-cell';
                        
                        if (i === 0) {{
                            cell.textContent = 'START';
                        }} else if (i === boardSize-1 || i === totalCells-1 || i === totalCells-boardSize) {{
                            cell.classList.add('cell-nasa');
                            cell.textContent = 'NASA';
                        }} else {{
                            const cellType = cellTypes[Math.floor(Math.random() * cellTypes.length)];
                            switch(cellType) {{
                                case 'problem': cell.textContent = 'PROB'; cell.classList.add('cell-problem'); break;
                                case 'opportunity': cell.textContent = 'OPP'; cell.classList.add('cell-opportunity'); break;
                                case 'asset': cell.textContent = 'ASSET'; cell.classList.add('cell-asset'); break;
                                case 'nasa-data': cell.textContent = 'NASA'; cell.classList.add('cell-nasa'); break;
                                case 'market': cell.textContent = 'MKT'; cell.classList.add('cell-market'); break;
                                case 'quiz': cell.textContent = 'QUIZ'; cell.classList.add('cell-quiz'); break;
                            }}
                        }}
                        
                        cell.addEventListener('click', function() {{
                            alert('You clicked: ' + this.textContent);
                        }});
                        
                        gameBoard.appendChild(cell);
                    }}
                }}

                function rollDice() {{
                    const dice = document.getElementById('dice');
                    const rolls = 10;
                    let count = 0;
                    
                    const rollInterval = setInterval(() => {{
                        const value = Math.floor(Math.random() * 6) + 1;
                        dice.textContent = value;
                        dice.style.transform = 'rotate(' + (count * 45) + 'deg)';
                        count++;
                        
                        if (count >= rolls) {{
                            clearInterval(rollInterval);
                            dice.style.transform = 'rotate(0deg)';
                            alert('You rolled a ' + value + '! Move ' + value + ' spaces.');
                        }}
                    }}, 100);
                }}

                document.addEventListener('DOMContentLoaded', initializeBoard);
            </script>
        </body>
        </html>
        """
        
        # Save HTML file
        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return html_content

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
st.markdown('<h1 style="text-align: center; color: #2E7D32;">🌾 Harvest Horizon</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #558B2F; font-size: 1.2rem;">Learn Sustainable Farming with NASA Satellite Data</p>', unsafe_allow_html=True)

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
        st.success("""
        **🎯 Your Mission**
        
        You're a farm manager using NASA satellite data to optimize your harvest. 
        Make smart decisions about irrigation and fertilization based on real climate data!
        
        **Goal:** Maximize yield while conserving resources.
        """)
        
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
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🚀 Start Farming", use_container_width=True, type="primary"):
                st.session_state.current_scenario = scenario_choice
                st.session_state.game = FarmingSimulator(SCENARIOS[scenario_choice])
                
                with st.spinner("Loading NASA satellite data..."):
                    st.session_state.game.load_nasa_data(st.session_state.nasa_fetcher)
                    time.sleep(1)
                
                st.session_state.game_state = 'playing'
                st.rerun()
        
        with col_btn2:
            if st.button("🎮 Multiplayer Game", use_container_width=True, type="secondary"):
                st.session_state.current_scenario = scenario_choice
                st.session_state.game = FarmingSimulator(SCENARIOS[scenario_choice])
                
                with st.spinner("Loading NASA satellite data and game board..."):
                    st.session_state.game.load_nasa_data(st.session_state.nasa_fetcher)
                    html_content = st.session_state.game.generate_html_dashboard(scenario_choice)
                    time.sleep(1)
                
                st.session_state.game_state = 'multi-playing'
                st.session_state.show_dashboard = True
                st.rerun()

# Show HTML dashboard if game is playing and dashboard exists
elif st.session_state.get('game_state') == 'multi-playing' and st.session_state.get('show_dashboard'):
    st.subheader("🎮 Harvest Horizon: The Satellite Steward - Multiplayer")
    
    if os.path.exists("dashboard.html"):
        # Use a reasonable height that works on most devices
        components.html(open("dashboard.html", "r", encoding="utf-8").read(), 
                       height=700,
                       scrolling=True)
    else:
        st.warning("Dashboard not yet generated.")
        
    # Back button
    if st.button("← Back to Main Menu", use_container_width=True):
        st.session_state.game_state = 'welcome'
        st.rerun()
            
elif st.session_state.game_state == 'playing':   
    
    game = st.session_state.game
    analysis = game.analyze_conditions()
    
    st.markdown("---")
    st.header("🌍 Step 1: Review NASA Satellite Data")
    
    # Metrics - use columns but they'll stack on mobile naturally
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
        st.warning(rec)
    
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
    
    st.warning("**⚠️ Think carefully!** Base your decisions on the NASA data above.")
    
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
        
        st.metric("Crop Yield", f"{yield_pct}%")
    
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
    st.success("""
    **NASA satellite data helps farmers:**
    
    ✅ Monitor soil moisture for optimal irrigation
    ✅ Track temperature and rainfall patterns  
    ✅ Make data-driven conservation decisions
    ✅ Improve yields sustainably (15-25% increase possible!)
    ✅ Save water (20-30% reduction with precision agriculture)
    """)
    
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
