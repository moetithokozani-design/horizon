"""
FarmSense - Complete NASA Agriculture Game

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

# Custom CSS with responsive design
st.markdown("""
    <style>
    /* Base responsive styles */
    .main-header {
        font-size: clamp(2rem, 5vw, 3rem);
        color: #2E7D32;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
        word-wrap: break-word;
    }
    .sub-header {
        font-size: clamp(1rem, 2.5vw, 1.3rem);
        color: #558B2F;
        text-align: center;
        margin-bottom: 30px;
        word-wrap: break-word;
    }
    .metric-card {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        padding: clamp(15px, 3vw, 20px);
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 10px 0;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .stat-big {
        font-size: clamp(1.8rem, 4vw, 2.5rem);
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
    }
    .recommendation {
        background: #FFF3E0;
        padding: clamp(12px, 2vw, 15px);
        border-radius: 8px;
        border-left: 4px solid #FF9800;
        margin: 10px 0;
        font-size: clamp(0.9rem, 1.5vw, 1rem);
    }
    .success-box {
        background: #E8F5E9;
        padding: clamp(15px, 3vw, 20px);
        border-radius: 10px;
        border: 2px solid #4CAF50;
        margin: 10px 0;
    }
    .warning-box {
        background: #FFF3E0;
        padding: clamp(15px, 3vw, 20px);
        border-radius: 10px;
        border: 2px solid #FF9800;
        margin: 10px 0;
    }
    .game-board {
        background: #1a3c27;
        padding: clamp(15px, 2vw, 20px);
        border-radius: 15px;
        border: 3px solid #8bc34a;
        margin: 20px 0;
    }
    
    /* Mobile-specific adjustments */
    @media (max-width: 768px) {
        .stButton button {
            width: 100%;
            margin: 5px 0;
        }
        .stRadio > div {
            flex-direction: column;
        }
        .stRadio label {
            margin-bottom: 10px;
        }
    }
    
    /* Ensure proper spacing on mobile */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Responsive metric containers */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    /* Responsive columns */
    .responsive-columns {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
    }
    
    /* Mobile-first button styles */
    .mobile-friendly-btn {
        min-height: 3rem;
        font-size: clamp(0.9rem, 2vw, 1.1rem);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Responsive text */
    .responsive-text {
        font-size: clamp(0.9rem, 1.5vw, 1rem);
        line-height: 1.5;
    }
    
    /* Chart responsiveness */
    .stPlotlyChart, .stPyplot {
        max-width: 100%;
        height: auto;
    }
    
    /* Sidebar adjustments for mobile */
    @media (max-width: 768px) {
        .sidebar .sidebar-content {
            padding: 1rem;
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
        """Generate the complete HTML game dashboard with responsive design"""
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
                    padding: clamp(10px, 3vw, 20px);
                    overflow-x: hidden;
                }}

                .container {{
                    max-width: min(1200px, 95vw);
                    margin: 0 auto;
                }}

                header {{
                    text-align: center;
                    padding: clamp(15px, 3vw, 20px) 0;
                    margin-bottom: clamp(15px, 3vw, 20px);
                    border-bottom: 2px solid rgba(139, 195, 74, 0.3);
                }}

                h1 {{
                    font-size: clamp(1.8rem, 6vw, 2.8rem);
                    margin-bottom: clamp(8px, 2vw, 10px);
                    background: linear-gradient(to right, #8bc34a, #4caf50, #2e7d32);
                    -webkit-background-clip: text;
                    background-clip: text;
                    color: transparent;
                    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
                    word-wrap: break-word;
                }}

                .subtitle {{
                    font-size: clamp(1rem, 3vw, 1.2rem);
                    color: #c8e6c9;
                    max-width: min(800px, 90vw);
                    margin: 0 auto;
                    line-height: 1.5;
                }}

                .game-board {{
                    width: 100%;
                    aspect-ratio: 1;
                    max-width: min(600px, 90vw);
                    margin: clamp(15px, 3vw, 20px) auto;
                    background: #1e4620;
                    border-radius: 10px;
                    border: 3px solid #8bc34a;
                    display: grid;
                    grid-template-columns: repeat(11, 1fr);
                    grid-template-rows: repeat(11, 1fr);
                    gap: 1px;
                    padding: 5px;
                    position: relative;
                    overflow: hidden;
                    box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.3);
                }}

                .board-cell {{
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 3px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: clamp(0.5rem, 1.5vw, 0.65rem);
                    text-align: center;
                    padding: 2px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: 500;
                    word-break: break-word;
                }}

                .board-cell:hover {{
                    background: rgba(255, 255, 255, 0.15);
                    transform: scale(1.05);
                }}

                .cell-problem {{ background: rgba(255, 87, 34, 0.4) !important; }}
                .cell-opportunity {{ background: rgba(76, 175, 80, 0.4) !important; }}
                .cell-asset {{ background: rgba(255, 193, 7, 0.4) !important; }}
                .cell-nasa {{ background: rgba(33, 150, 243, 0.4) !important; }}
                .cell-market {{ background: rgba(156, 39, 176, 0.4) !important; }}
                .cell-quiz {{ background: rgba(0, 188, 212, 0.4) !important; }}

                .player-token {{
                    width: clamp(20px, 4vw, 28px);
                    height: clamp(20px, 4vw, 28px);
                    border-radius: 50%;
                    position: absolute;
                    border: 2px solid white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: clamp(10px, 2vw, 12px);
                    transition: all 0.5s ease;
                    z-index: 10;
                    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
                }}

                .game-controls {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: clamp(8px, 2vw, 10px);
                    justify-content: center;
                    margin-bottom: clamp(15px, 3vw, 20px);
                    padding: 0 clamp(10px, 3vw, 20px);
                }}

                .control-btn {{
                    padding: clamp(10px, 2vw, 12px) clamp(15px, 3vw, 20px);
                    background: rgba(255, 255, 255, 0.1);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 25px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: 500;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    font-size: clamp(0.8rem, 2vw, 1rem);
                    text-align: center;
                    min-height: 44px; /* Mobile touch friendly */
                }}

                .control-btn:hover {{
                    background: rgba(255, 255, 255, 0.2);
                    transform: translateY(-2px);
                }}

                .dashboard {{
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    padding: clamp(15px, 3vw, 20px);
                    display: flex;
                    flex-direction: column;
                    margin: clamp(15px, 3vw, 20px) auto;
                    max-width: min(500px, 90vw);
                }}

                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                    gap: clamp(8px, 2vw, 12px);
                    margin-bottom: clamp(15px, 3vw, 20px);
                }}

                .stat-card {{
                    background: rgba(0, 0, 0, 0.2);
                    padding: clamp(12px, 2vw, 15px);
                    border-radius: 10px;
                    border-left: 4px solid #4caf50;
                    transition: all 0.3s ease;
                    min-height: 80px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }}

                .stat-card h3 {{
                    font-size: clamp(0.8rem, 2vw, 0.9rem);
                    color: #c8e6c9;
                    margin-bottom: 8px;
                }}

                .stat-value {{
                    font-size: clamp(1.2rem, 3vw, 1.4rem);
                    font-weight: bold;
                }}

                /* Mobile-specific adjustments */
                @media (max-width: 480px) {{
                    .game-board {{
                        grid-template-columns: repeat(11, 1fr);
                        grid-template-rows: repeat(11, 1fr);
                        gap: 1px;
                    }}
                    
                    .board-cell {{
                        font-size: 0.5rem;
                        padding: 1px;
                    }}
                    
                    .game-controls {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .stats-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}

                /* Tablet adjustments */
                @media (min-width: 481px) and (max-width: 768px) {{
                    .game-controls {{
                        grid-template-columns: repeat(2, 1fr);
                    }}
                    
                    .stats-grid {{
                        grid-template-columns: repeat(2, 1fr);
                    }}
                }}

                /* Large screen adjustments */
                @media (min-width: 1200px) {{
                    .game-board {{
                        max-width: 600px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Harvest Horizon: The Satellite Steward</h1>
                    <p class="subtitle">Roll the dice, manage your farm with NASA data, and achieve agricultural resilience!</p>
                </header>

                <div class="game-controls">
                    <button class="control-btn" onclick="showModal('region-modal')">🌍 Change Region</button>
                    <button class="control-btn" onclick="showModal('climate-modal')">🌡️ Climate</button>
                    <button class="control-btn" onclick="showModal('players-modal')">👥 Players</button>
                    <button class="control-btn" onclick="showModal('resources-modal')">🛰️ NASA Resources</button>
                    <button class="control-btn" onclick="resetGame()">🔄 Reset Game</button>
                </div>

                <div class="game-board" id="game-board">
                    <!-- Board cells will be generated by JavaScript -->
                </div>

                <div class="dashboard">
                    <div class="turn-indicator" id="turn-indicator">
                        Player 1's Turn - Roll the dice!
                    </div>

                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>CASH ON HAND</h3>
                            <div class="stat-value" id="cash">$10,000</div>
                        </div>
                        <div class="stat-card">
                            <h3>PASSIVE INCOME</h3>
                            <div class="stat-value" id="passive-income">$500</div>
                        </div>
                        <div class="stat-card">
                            <h3>MONTHLY EXPENSES</h3>
                            <div class="stat-value" id="expenses">$3,000</div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // Initialize game board
                function initializeBoard() {{
                    const gameBoard = document.getElementById('game-board');
                    const boardSize = 11;
                    const totalCells = boardSize * boardSize;
                    const cellTypes = ['problem', 'opportunity', 'asset', 'nasa-data', 'market', 'quiz'];
                    
                    for (let i = 0; i < totalCells; i++) {{
                        const cell = document.createElement('div');
                        cell.className = 'board-cell';
                        
                        if (i === 0) {{
                            cell.classList.add('corner-cell');
                            cell.textContent = 'START';
                        }} else if (i === boardSize-1 || i === totalCells-1 || i === totalCells-boardSize) {{
                            cell.classList.add('corner-cell', 'cell-nasa');
                            cell.textContent = 'NASA';
                        }} else {{
                            const cellType = cellTypes[Math.floor(Math.random() * cellTypes.length)];
                            let displayText = '';
                            
                            switch(cellType) {{
                                case 'problem': displayText = 'PROB'; cell.classList.add('cell-problem'); break;
                                case 'opportunity': displayText = 'OPP'; cell.classList.add('cell-opportunity'); break;
                                case 'asset': displayText = 'ASSET'; cell.classList.add('cell-asset'); break;
                                case 'nasa-data': displayText = 'NASA'; cell.classList.add('cell-nasa'); break;
                                case 'market': displayText = 'MKT'; cell.classList.add('cell-market'); break;
                                case 'quiz': displayText = 'QUIZ'; cell.classList.add('cell-quiz'); break;
                            }}
                            
                            cell.textContent = displayText;
                        }}
                        
                        cell.addEventListener('click', function() {{
                            alert('You clicked: ' + this.textContent + '\\nThis is where educational content would appear!');
                        }});
                        
                        gameBoard.appendChild(cell);
                    }}
                }}

                // Initialize when page loads
                document.addEventListener('DOMContentLoaded', initializeBoard);

                // Handle window resize
                window.addEventListener('resize', function() {{
                    // Board automatically adjusts due to CSS
                    console.log('Screen resized - board should be responsive');
                }});

                // Placeholder functions for game features
                function showModal(modalId) {{
                    alert('Modal: ' + modalId + ' would open here');
                }}

                function resetGame() {{
                    if (confirm('Reset the game?')) {{
                        location.reload();
                    }}
                }}
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

# Header with responsive design
st.markdown('<p class="main-header">🌾 Harvest Horizon</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Learn Sustainable Farming with NASA Satellite Data</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📖 About Harvest Horizon")
    st.markdown('<div class="responsive-text">', unsafe_allow_html=True)
    st.write("""
    Use real NASA satellite data to make smart farming decisions!
    
    **Learn about:**
    - Temperature monitoring
    - Soil moisture analysis
    - Precipitation patterns
    - Sustainable practices
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    st.header("🛰️ NASA Data Sources")
    st.markdown('<div class="responsive-text">', unsafe_allow_html=True)
    st.write("""
    - **T2M**: Temperature at 2m
    - **PRECTOTCORR**: Precipitation
    - **GWETROOT**: Soil Moisture
    - **ALLSKY_SFC_SW_DWN**: Solar Radiation
    
    *Data: NASA POWER API*
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    if st.button("🔄 Restart Game", use_container_width=True, key="restart_btn"):
        st.session_state.game_state = 'welcome'
        st.session_state.game = None
        st.session_state.results = None
        st.rerun()

# Main Game Logic
if st.session_state.game_state == 'welcome':
    st.markdown("---")
    
    # Responsive columns for welcome screen
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="success-box">
        <h3 style="color: green; font-size: clamp(1.2rem, 3vw, 1.5rem);">🎯 Your Mission</h3>
        <p style="color: green; font-size: clamp(0.9rem, 2vw, 1rem);">You're a farm manager using NASA satellite data to optimize your harvest. 
        Make smart decisions about irrigation and fertilization based on real climate data!</p>
        <p style="color: green; font-size: clamp(0.9rem, 2vw, 1rem);"><strong>Goal:</strong> Maximize yield while conserving resources.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.subheader("Choose Your Farm:")
        
        # Responsive scenario selection
        scenario_choice = st.radio(
            "Select difficulty level:",
            options=list(SCENARIOS.keys()),
            format_func=lambda x: f"{SCENARIOS[x]['name']} - {SCENARIOS[x]['difficulty']}",
            key='scenario_select'
        )
        
        st.info(SCENARIOS[scenario_choice]['description'])
        
        st.write("")
        
        # Responsive button layout
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🚀 Start Farming", use_container_width=True, type="primary", key="start_farming"):
                st.session_state.current_scenario = scenario_choice
                st.session_state.game = FarmingSimulator(SCENARIOS[scenario_choice])
                
                with st.spinner("Loading NASA satellite data..."):
                    st.session_state.game.load_nasa_data(st.session_state.nasa_fetcher)
                    time.sleep(1)
                
                st.session_state.game_state = 'playing'
                st.rerun()
        
        with col_btn2:
            if st.button("🎮 Multiplayer Game", use_container_width=True, type="secondary", key="multiplayer"):
                st.session_state.current_scenario = scenario_choice
                st.session_state.game = FarmingSimulator(SCENARIOS[scenario_choice])
                
                with st.spinner("Loading NASA satellite data and game board..."):
                    st.session_state.game.load_nasa_data(st.session_state.nasa_fetcher)
                    # Generate the HTML dashboard
                    html_content = st.session_state.game.generate_html_dashboard(scenario_choice)
                    time.sleep(1)
                
                st.session_state.game_state = 'multi-playing'
                st.session_state.show_dashboard = True
                st.rerun()

# Show HTML dashboard if game is playing and dashboard exists
elif st.session_state.get('game_state') == 'multi-playing' and st.session_state.get('show_dashboard'):
    st.subheader("🎮 Harvest Horizon: The Satellite Steward - Multiplayer")
    
    # Responsive container for the HTML game
    if os.path.exists("dashboard.html"):
        # Use responsive height based on screen size
        components.html(open("dashboard.html", "r", encoding="utf-8").read(), 
                       height=800,  # Fixed height that works on most devices
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
    
    # Responsive metrics grid
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recommendations
    st.markdown("---")
    st.subheader("💡 NASA Data Insights")
    
    recs = game.generate_recommendations(analysis)
    for rec in recs:
        st.markdown(f'<div class="recommendation">{rec}</div>', unsafe_allow_html=True)
    
    # Responsive visualization columns
    with st.expander("📊 View Detailed Data Charts"):
        st.markdown('<div class="responsive-columns">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Recent Temperature Trend**")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(range(1, 11), analysis['temp_data'], 'r-o', linewidth=2)
            ax.set_xlabel('Days Ago')
            ax.set_ylabel('Temperature (°C)')
            ax.grid(True, alpha=0.3)
            st.pyplot(fig, use_container_width=True)
            plt.close()
        
        with col2:
            st.write("**Recent Precipitation**")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.bar(range(1, 11), analysis['precip_data'], color='skyblue')
            ax.set_xlabel('Days Ago')
            ax.set_ylabel('Rainfall (mm)')
            ax.grid(True, alpha=0.3, axis='y')
            st.pyplot(fig, use_container_width=True)
            plt.close()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Decision Making
    st.markdown("---")
    st.header("🎮 Step 2: Make Your Farming Decisions")
    
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ Think carefully!</strong> Base your decisions on the NASA data above.
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # Responsive decision columns
    st.markdown('<div class="responsive-columns">', unsafe_allow_html=True)
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
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    
    # Responsive harvest button
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
    
    # Big yield display with responsive layout
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
    
    # Responsive results columns
    st.markdown('<div class="responsive-columns">', unsafe_allow_html=True)
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
        st.pyplot(fig, use_container_width=True)
        plt.close()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    
    # Responsive button layout
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
<div style='text-align: center; color: #666; padding: 20px; font-size: clamp(0.8rem, 2vw, 1rem);'>
    <p><strong>FarmSense</strong> - NASA Space Apps Challenge 2025</p>
    <p>Data Source: NASA POWER API | Built with Python & Streamlit</p>
    <p>🌾 Empowering sustainable agriculture through space technology 🛰️</p>
</div>
""", unsafe_allow_html=True)
