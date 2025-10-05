import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def plot_temperature_trend(nasa_data):
    """
    Create temperature trend visualization
    Team Member 2: Customize colors and labels as needed
    """
    if not nasa_data:
        return None
    
    params = nasa_data['properties']['parameter']
    temp_data = params['T2M']
    
    # Convert to DataFrame
    dates = [datetime.strptime(d, '%Y%m%d') for d in temp_data.keys()]
    temps = list(temp_data.values())
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dates, temps, color='#FF6B6B', linewidth=2, marker='o', markersize=4)
    ax.fill_between(dates, temps, alpha=0.3, color='#FF6B6B')
    
    ax.set_title('Temperature Trend (Last 30 Days)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('Temperature (°C)', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

def plot_precipitation_bars(nasa_data):
    """
    Create precipitation bar chart
    Team Member 2: Adjust styling to match game theme
    """
    if not nasa_data:
        return None
    
    params = nasa_data['properties']['parameter']
    precip_data = params['PRECTOTCORR']
    
    # Convert to DataFrame
    dates = [datetime.strptime(d, '%Y%m%d') for d in precip_data.keys()]
    precip = list(precip_data.values())
    
    fig, ax = plt.subplots(figsize=(10, 4))
    bars = ax.bar(dates, precip, color='#4ECDC4', alpha=0.7, edgecolor='#2C7873')
    
    # Highlight days with high rainfall
    for i, (bar, val) in enumerate(zip(bars, precip)):
        if val > 5:
            bar.set_color('#FF6B6B')
    
    ax.set_title('Precipitation (Last 30 Days)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('Rainfall (mm)', fontsize=11)
    ax.axhline(y=2.5, color='orange', linestyle='--', label='Low rainfall threshold', alpha=0.7)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

def plot_soil_moisture_gauge(current_moisture):
    """
    Create soil moisture gauge/meter
    Team Member 2: Make this visually appealing!
    """
    fig, ax = plt.subplots(figsize=(6, 4), subplot_kw=dict(aspect="equal"))
    
    # Define moisture levels
    categories = ['Dry\n0-0.3', 'Optimal\n0.3-0.5', 'Wet\n0.5-1.0']
    values = [0.3, 0.2, 0.5]
    colors = ['#FFB6B9', '#8FD14F', '#4A90E2']
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        values,
        labels=categories,
        colors=colors,
        autopct='',
        startangle=90,
        counterclock=False
    )
    
    # Add current moisture indicator
    angle = 90 - (current_moisture * 180)  # Convert moisture to angle
    ax.annotate(
        '', 
        xy=(0.6*np.cos(np.radians(angle)), 0.6*np.sin(np.radians(angle))),
        xytext=(0, 0),
        arrowprops=dict(arrowstyle='->', lw=3, color='black')
    )
    
    ax.set_title(f'Current Soil Moisture: {current_moisture:.2f}', 
                 fontsize=12, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig

def plot_comparison_chart(player_decisions, optimal_decisions):
    """
    Compare player decisions vs optimal
    Team Member 2: Show how well player did!
    """
    categories = ['Irrigation', 'Fertilizer']
    player_vals = [player_decisions['irrigation'], player_decisions['fertilizer']]
    optimal_vals = [optimal_decisions['irrigation'], optimal_decisions['fertilizer']]
    
    x = np.arange(len(categories))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar(x - width/2, player_vals, width, label='Your Decision', 
                    color='#FF6B6B', alpha=0.8)
    bars2 = ax.bar(x + width/2, optimal_vals, width, label='Optimal', 
                    color='#8FD14F', alpha=0.8)
    
    ax.set_ylabel('Amount (units)', fontsize=11)
    ax.set_title('Your Decisions vs Optimal', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    return fig

def create_yield_progress_bar(yield_pct):
    """
    Create visual progress bar for yield
    Team Member 2: Make this eye-catching!
    """
    fig, ax = plt.subplots(figsize=(10, 2))
    
    # Determine color based on performance
    if yield_pct > 110:
        color = '#8FD14F'
        label = 'Excellent!'
    elif yield_pct > 90:
        color = '#4ECDC4'
        label = 'Good'
    elif yield_pct > 70:
        color = '#FFB347'
        label = 'Fair'
    else:
        color = '#FF6B6B'
        label = 'Needs Improvement'
    
    # Create horizontal bar
    ax.barh([0], [yield_pct], height=0.5, color=color, alpha=0.8, edgecolor='black', linewidth=2)
    ax.barh([0], [150], height=0.5, color='lightgray', alpha=0.3, zorder=0)
    
    # Add text
    ax.text(yield_pct/2, 0, f'{yield_pct}% - {label}', 
            ha='center', va='center', fontsize=16, fontweight='bold', color='white')
    
    ax.set_xlim(0, 150)
    ax.set_ylim(-0.5, 0.5)
    ax.axis('off')
    ax.set_title('Crop Yield Performance', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig

def plot_multi_parameter_timeline(nasa_data):
    """
    Advanced: Plot multiple parameters on same timeline
    Team Member 2: Optional - only if time permits!
    """
    if not nasa_data:
        return None
    
    params = nasa_data['properties']['parameter']
    
    dates = [datetime.strptime(d, '%Y%m%d') for d in params['T2M'].keys()]
    temps = list(params['T2M'].values())
    precip = list(params['PRECTOTCORR'].values())
    soil = list(params['GWETROOT'].values())
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    
    # Temperature
    ax1.plot(dates, temps, color='#FF6B6B', linewidth=2)
    ax1.fill_between(dates, temps, alpha=0.3, color='#FF6B6B')
    ax1.set_ylabel('Temp (°C)', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Multi-Parameter Analysis', fontsize=14, fontweight='bold')
    
    # Precipitation
    ax2.bar(dates, precip, color='#4ECDC4', alpha=0.7)
    ax2.set_ylabel('Precip (mm)', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Soil Moisture
    ax3.plot(dates, soil, color='#8FD14F', linewidth=2, marker='o', markersize=3)
    ax3.fill_between(dates, soil, alpha=0.3, color='#8FD14F')
    ax3.axhspan(0.3, 0.5, alpha=0.2, color='green', label='Optimal range')
    ax3.set_ylabel('Soil Moisture', fontsize=10)
    ax3.set_xlabel('Date', fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    ax3.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

# Helper function to integrate with Streamlit
def display_nasa_charts(st, nasa_data):
    """
    Easy function for UI team to call
    Usage in main app: display_nasa_charts(st, game.nasa_data)
    """
    st.subheader("📊 Detailed NASA Data Visualization")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🌡️ Temperature", "🌧️ Precipitation", "💧 Soil Moisture", "📈 All Data"])
    
    with tab1:
        fig = plot_temperature_trend(nasa_data)
        if fig:
            st.pyplot(fig)
    
    with tab2:
        fig = plot_precipitation_bars(nasa_data)
        if fig:
            st.pyplot(fig)
    
    with tab3:
        if nasa_data:
            params = nasa_data['properties']['parameter']
            soil_values = list(params['GWETROOT'].values())
            current_moisture = soil_values[-1] if soil_values else 0.4
            fig = plot_soil_moisture_gauge(current_moisture)
            st.pyplot(fig)
    
    with tab4:
        fig = plot_multi_parameter_timeline(nasa_data)
        if fig:
            st.pyplot(fig)

# Export all functions
__all__ = [
    'plot_temperature_trend',
    'plot_precipitation_bars', 
    'plot_soil_moisture_gauge',
    'plot_comparison_chart',
    'create_yield_progress_bar',
    'plot_multi_parameter_timeline',
    'display_nasa_charts'
]
