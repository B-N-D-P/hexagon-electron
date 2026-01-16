#!/usr/bin/env python3
"""
Enhanced Structural Repair Quality Analysis Report
Includes Hexagon Radar Chart, All Graphs, and Professional Layout
"""

import json
import base64
from io import BytesIO
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_hexagon_chart(quality_data):
    """
    Create a hexagon (radar chart) showing all quality metrics
    """
    categories = [
        'Frequency<br>Recovery',
        'Mode Shape<br>Match',
        'Damping<br>Recovery',
        'Overall<br>Quality',
        'Structural<br>Integrity',
        'Repair<br>Effectiveness'
    ]
    
    # Extract scores (0-1 range)
    freq_recovery = quality_data.get('frequency', 0)
    mode_shape = quality_data.get('mode_shape', 0)
    damping = quality_data.get('damping', 0)
    overall = quality_data.get('overall', 0)
    
    # Calculate derived metrics
    structural_integrity = (freq_recovery + damping) / 2
    repair_effectiveness = (mode_shape + overall) / 2
    
    values = [
        freq_recovery * 100,
        mode_shape * 100,
        damping * 100,
        overall * 100,
        structural_integrity * 100,
        repair_effectiveness * 100
    ]
    
    # Close the chart (repeat first value at end)
    values += values[:1]
    categories_plot = categories + [categories[0]]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories_plot,
        fill='toself',
        fillcolor='rgba(102, 126, 234, 0.4)',
        line=dict(color='rgba(102, 126, 234, 0.8)', width=2),
        marker=dict(size=8, color='rgba(102, 126, 234, 1)'),
        name='Quality Metrics'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color='#a0a0a0'),
                gridcolor='rgba(102, 126, 234, 0.2)',
                showline=True,
                linecolor='rgba(102, 126, 234, 0.3)'
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color='#e0e6ed'),
                gridcolor='rgba(102, 126, 234, 0.3)'
            ),
            bgcolor='rgba(15, 52, 96, 0.3)'
        ),
        showlegend=False,
        hovermode='closest',
        title=dict(
            text='<b>Quality Metrics Hexagon (Radar Chart)</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=16, color='#e0e6ed')
        ),
        height=500,
        width=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#e0e6ed')
    )
    
    return fig

def create_frequency_comparison_chart(modal_data):
    """
    Create bar chart comparing frequencies across states
    """
    modes = list(range(1, len(modal_data['original']['natural_frequencies_hz']) + 1))
    
    fig = go.Figure(data=[
        go.Bar(
            x=modes,
            y=modal_data['original']['natural_frequencies_hz'],
            name='Original',
            marker=dict(color='rgba(0, 217, 255, 0.8)'),
            hovertemplate='<b>Mode %{x}</b><br>Frequency: %{y:.2f} Hz<extra></extra>'
        ),
        go.Bar(
            x=modes,
            y=modal_data['damaged']['natural_frequencies_hz'],
            name='Damaged',
            marker=dict(color='rgba(255, 107, 107, 0.8)'),
            hovertemplate='<b>Mode %{x}</b><br>Frequency: %{y:.2f} Hz<extra></extra>'
        ),
        go.Bar(
            x=modes,
            y=modal_data['repaired']['natural_frequencies_hz'],
            name='Repaired',
            marker=dict(color='rgba(76, 175, 80, 0.8)'),
            hovertemplate='<b>Mode %{x}</b><br>Frequency: %{y:.2f} Hz<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='<b>Frequency Comparison Across States</b>',
        xaxis_title='Mode Number',
        yaxis_title='Frequency (Hz)',
        barmode='group',
        hovermode='x unified',
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 52, 96, 0.3)',
        xaxis=dict(
            gridcolor='rgba(102, 126, 234, 0.2)',
            tickfont=dict(color='#a0a0a0'),
            title_font=dict(color='#e0e6ed')
        ),
        yaxis=dict(
            gridcolor='rgba(102, 126, 234, 0.2)',
            tickfont=dict(color='#a0a0a0'),
            title_font=dict(color='#e0e6ed')
        ),
        legend=dict(
            x=1.02,
            y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(0, 0, 0, 0.3)',
            bordercolor='rgba(102, 126, 234, 0.5)',
            borderwidth=1
        ),
        font=dict(family='Inter, sans-serif', color='#e0e6ed')
    )
    
    return fig

def create_quality_breakdown_chart(quality_data):
    """
    Create pie/donut chart for quality breakdown
    """
    labels = ['Frequency Recovery', 'Mode Shape Match', 'Damping Recovery']
    values = [
        quality_data.get('frequency', 0) * 100,
        quality_data.get('mode_shape', 0) * 100,
        quality_data.get('damping', 0) * 100
    ]
    
    colors = ['rgba(255, 193, 7, 0.8)', 'rgba(76, 175, 80, 0.8)', 'rgba(0, 217, 255, 0.8)']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color='#0f3460', width=2)),
        hovertemplate='<b>%{label}</b><br>Score: %{value:.1f}%<extra></extra>',
        textposition='inside',
        textinfo='label+percent'
    )])
    
    fig.update_layout(
        title='<b>Quality Breakdown (%)</b>',
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#e0e6ed'),
        legend=dict(
            x=1.05,
            y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(0, 0, 0, 0.3)',
            bordercolor='rgba(102, 126, 234, 0.5)',
            borderwidth=1
        )
    )
    
    return fig

def create_recovery_trajectory_chart(modal_data):
    """
    Create line chart showing recovery trajectory from damaged to repaired
    """
    modes = list(range(1, len(modal_data['original']['natural_frequencies_hz']) + 1))
    
    original_freqs = modal_data['original']['natural_frequencies_hz']
    damaged_freqs = modal_data['damaged']['natural_frequencies_hz']
    repaired_freqs = modal_data['repaired']['natural_frequencies_hz']
    
    fig = go.Figure()
    
    for mode_idx, mode in enumerate(modes):
        fig.add_trace(go.Scatter(
            x=['Original', 'Damaged', 'Repaired'],
            y=[original_freqs[mode_idx], damaged_freqs[mode_idx], repaired_freqs[mode_idx]],
            mode='lines+markers',
            name=f'Mode {mode}',
            hovertemplate='<b>Mode %{customdata}</b><br>%{x}<br>Frequency: %{y:.2f} Hz<extra></extra>',
            customdata=[mode] * 3,
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title='<b>Frequency Recovery Trajectory</b>',
        xaxis_title='Structure State',
        yaxis_title='Frequency (Hz)',
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 52, 96, 0.3)',
        xaxis=dict(
            gridcolor='rgba(102, 126, 234, 0.2)',
            tickfont=dict(color='#a0a0a0'),
            title_font=dict(color='#e0e6ed')
        ),
        yaxis=dict(
            gridcolor='rgba(102, 126, 234, 0.2)',
            tickfont=dict(color='#a0a0a0'),
            title_font=dict(color='#e0e6ed')
        ),
        hovermode='x unified',
        font=dict(family='Inter, sans-serif', color='#e0e6ed'),
        legend=dict(
            x=1.02,
            y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(0, 0, 0, 0.3)',
            bordercolor='rgba(102, 126, 234, 0.5)',
            borderwidth=1
        )
    )
    
    return fig

def create_damping_comparison_chart(modal_data):
    """Create damping ratio comparison chart"""
    modes = list(range(1, len(modal_data['original']['frequencies']) + 1))
    
    fig = go.Figure(data=[
        go.Bar(
            x=modes,
            y=[d * 100 for d in modal_data['original'].get('damping', [0]*5)],
            name='Original',
            marker=dict(color='rgba(0, 217, 255, 0.8)')
        ),
        go.Bar(
            x=modes,
            y=[d * 100 for d in modal_data['damaged'].get('damping', [0]*5)],
            name='Damaged',
            marker=dict(color='rgba(255, 107, 107, 0.8)')
        ),
        go.Bar(
            x=modes,
            y=[d * 100 for d in modal_data['repaired'].get('damping', [0]*5)],
            name='Repaired',
            marker=dict(color='rgba(76, 175, 80, 0.8)')
        )
    ])
    
    fig.update_layout(
        title='<b>Damping Ratio Comparison (%)</b>',
        xaxis_title='Mode',
        yaxis_title='Damping (%)',
        barmode='group',
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 52, 96, 0.3)',
        font=dict(family='Inter, sans-serif', color='#e0e6ed')
    )
    return fig

def create_energy_distribution_chart(modal_data):
    """Create energy distribution chart"""
    modes = list(range(1, len(modal_data['original']['frequencies']) + 1))
    
    # Estimate energy distribution (proportional to frequency * damping)
    orig_energy = [modal_data['original']['frequencies'][i] * 10 for i in range(len(modes))]
    total_energy = sum(orig_energy)
    orig_energy_pct = [e/total_energy*100 for e in orig_energy]
    
    fig = go.Figure(data=[
        go.Bar(
            x=modes,
            y=orig_energy_pct,
            marker=dict(color='rgba(0, 217, 255, 0.8)'),
            name='Energy Distribution'
        )
    ])
    
    fig.update_layout(
        title='<b>Modal Energy Distribution</b>',
        xaxis_title='Mode',
        yaxis_title='Energy (%)',
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 52, 96, 0.3)',
        font=dict(family='Inter, sans-serif', color='#e0e6ed')
    )
    return fig

def create_frequency_shift_chart(modal_data):
    """Create frequency shift analysis chart"""
    modes = list(range(1, len(modal_data['original']['frequencies']) + 1))
    
    orig_freqs = modal_data['original']['frequencies']
    dmg_freqs = modal_data['damaged']['frequencies']
    rep_freqs = modal_data['repaired']['frequencies']
    
    dmg_shift = [(dmg_freqs[i] - orig_freqs[i])/orig_freqs[i]*100 for i in range(len(modes))]
    rep_shift = [(rep_freqs[i] - orig_freqs[i])/orig_freqs[i]*100 for i in range(len(modes))]
    
    fig = go.Figure(data=[
        go.Scatter(
            x=modes,
            y=dmg_shift,
            mode='lines+markers',
            name='Damaged vs Original',
            line=dict(color='rgba(255, 107, 107, 0.8)', width=3),
            marker=dict(size=8)
        ),
        go.Scatter(
            x=modes,
            y=rep_shift,
            mode='lines+markers',
            name='Repaired vs Original',
            line=dict(color='rgba(76, 175, 80, 0.8)', width=3),
            marker=dict(size=8)
        )
    ])
    
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(102, 126, 234, 0.5)")
    
    fig.update_layout(
        title='<b>Frequency Shift Analysis (%)</b>',
        xaxis_title='Mode',
        yaxis_title='Frequency Shift (%)',
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 52, 96, 0.3)',
        hovermode='x unified',
        font=dict(family='Inter, sans-serif', color='#e0e6ed')
    )
    return fig

def create_mode_summary_chart(modal_data):
    """Create mode summary heatmap"""
    modes = list(range(1, len(modal_data['original']['frequencies']) + 1))
    
    orig_freqs = modal_data['original']['frequencies']
    dmg_freqs = modal_data['damaged']['frequencies']
    rep_freqs = modal_data['repaired']['frequencies']
    
    # Create a summary matrix
    z_data = [orig_freqs, dmg_freqs, rep_freqs]
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=modes,
        y=['Original', 'Damaged', 'Repaired'],
        colorscale='Viridis',
        text=[[f'{v:.2f}' for v in row] for row in z_data],
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title='Freq (Hz)')
    ))
    
    fig.update_layout(
        title='<b>Modal Summary Heatmap</b>',
        xaxis_title='Mode',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#e0e6ed')
    )
    return fig

def fig_to_html(fig):
    """Convert Plotly figure to HTML div"""
    return fig.to_html(include_plotlyjs=False, div_id=None)

def create_enhanced_report(analysis_data, modal_data, quality_data, output_file="enhanced_report.html"):
    """
    Create comprehensive enhanced HTML report with all visualizations
    """
    
    # Generate all charts
    hexagon_chart = create_hexagon_chart(quality_data)
    freq_chart = create_frequency_comparison_chart(modal_data)
    quality_chart = create_quality_breakdown_chart(quality_data)
    trajectory_chart = create_recovery_trajectory_chart(modal_data)
    
    # Create additional graphs for completeness
    damping_chart = create_damping_comparison_chart(modal_data)
    energy_chart = create_energy_distribution_chart(modal_data)
    frequency_shift_chart = create_frequency_shift_chart(modal_data)
    mode_summary_chart = create_mode_summary_chart(modal_data)
    
    # Convert to HTML
    hexagon_html = fig_to_html(hexagon_chart)
    freq_html = fig_to_html(freq_chart)
    quality_html = fig_to_html(quality_chart)
    trajectory_html = fig_to_html(trajectory_chart)
    damping_html = fig_to_html(damping_chart)
    energy_html = fig_to_html(energy_chart)
    frequency_shift_html = fig_to_html(frequency_shift_chart)
    mode_summary_html = fig_to_html(mode_summary_chart)
    
    # Prepare data for display
    interpretation = quality_data.get('interpretation', 'Analysis Complete')
    overall_score = quality_data.get('overall', 0) * 100
    
    original_freqs = modal_data['original']['natural_frequencies_hz'][:5]
    damaged_freqs = modal_data['damaged']['natural_frequencies_hz'][:5]
    repaired_freqs = modal_data['repaired']['natural_frequencies_hz'][:5]
    
    # HTML Template
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Structural Repair Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%);
            color: #e0e6ed;
            line-height: 1.8;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 60px;
            padding: 60px 40px;
            background: rgba(102, 126, 234, 0.1);
            border: 2px solid rgba(102, 126, 234, 0.5);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #66feff;
            text-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
        }}
        
        .subtitle {{
            font-size: 1.2em;
            color: #a0a0a0;
            margin-bottom: 20px;
        }}
        
        .score-display {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 30px;
            flex-wrap: wrap;
        }}
        
        .score-card {{
            background: rgba(15, 52, 96, 0.5);
            padding: 20px 40px;
            border-radius: 10px;
            border: 1px solid rgba(102, 126, 234, 0.3);
            min-width: 200px;
        }}
        
        .score-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #66feff;
        }}
        
        .score-label {{
            font-size: 0.9em;
            color: #a0a0a0;
            margin-top: 5px;
        }}
        
        .interpretation {{
            font-size: 1.3em;
            color: #66feff;
            margin-top: 20px;
            font-weight: 600;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 60px 0;
        }}
        
        .chart-container {{
            background: rgba(15, 52, 96, 0.3);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }}
        
        .full-width {{
            grid-column: 1 / -1;
        }}
        
        .modal-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            background: rgba(15, 52, 96, 0.3);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .modal-table th {{
            background: rgba(102, 126, 234, 0.2);
            padding: 15px;
            text-align: left;
            border-bottom: 2px solid rgba(102, 126, 234, 0.5);
            font-weight: 600;
            color: #66feff;
        }}
        
        .modal-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid rgba(102, 126, 234, 0.2);
        }}
        
        .modal-table tr:hover {{
            background: rgba(102, 126, 234, 0.1);
        }}
        
        .section {{
            margin: 60px 0;
            padding: 40px;
            background: rgba(15, 52, 96, 0.3);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }}
        
        .section h2 {{
            font-size: 1.8em;
            color: #66feff;
            margin-bottom: 25px;
            border-bottom: 2px solid rgba(102, 126, 234, 0.3);
            padding-bottom: 15px;
        }}
        
        .metrics-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .metric-box {{
            background: rgba(102, 126, 234, 0.1);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid rgba(102, 126, 234, 0.8);
        }}
        
        .metric-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #66feff;
        }}
        
        .metric-label {{
            font-size: 0.9em;
            color: #a0a0a0;
            margin-top: 5px;
        }}
        
        .recommendations {{
            background: rgba(76, 175, 80, 0.1);
            border-left: 4px solid rgba(76, 175, 80, 0.8);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .recommendations h3 {{
            color: #76ba1b;
            margin-bottom: 15px;
        }}
        
        .recommendations ul {{
            margin-left: 20px;
        }}
        
        .recommendations li {{
            margin: 10px 0;
            color: #a0a0a0;
        }}
        
        footer {{
            text-align: center;
            margin-top: 60px;
            padding-top: 30px;
            border-top: 1px solid rgba(102, 126, 234, 0.3);
            color: #a0a0a0;
        }}
        
        .timestamp {{
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏗️ Structural Repair Quality Analysis</h1>
            <p class="subtitle">Comprehensive Modal Parameter Assessment & Repair Effectiveness Evaluation</p>
            <div class="score-display">
                <div class="score-card">
                    <div class="score-value">{overall_score:.1f}%</div>
                    <div class="score-label">Overall Quality</div>
                </div>
                <div class="score-card">
                    <div class="score-value">{quality_data.get('frequency', 0)*100:.1f}%</div>
                    <div class="score-label">Frequency Recovery</div>
                </div>
                <div class="score-card">
                    <div class="score-value">{quality_data.get('mode_shape', 0)*100:.1f}%</div>
                    <div class="score-label">Mode Shape Match</div>
                </div>
                <div class="score-card">
                    <div class="score-value">{quality_data.get('damping', 0)*100:.1f}%</div>
                    <div class="score-label">Damping Recovery</div>
                </div>
            </div>
            <div class="interpretation">
                📊 Status: <span style="color: #66feff;">{interpretation}</span>
            </div>
        </header>
        
        <div class="section">
            <h2>📈 Quality Metrics Visualization</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    {hexagon_html}
                </div>
                <div class="chart-container">
                    {quality_html}
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔊 Frequency Analysis</h2>
            <div class="charts-grid full-width">
                <div class="chart-container">
                    {freq_html}
                </div>
            </div>
            
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Mode</th>
                        <th>Original (Hz)</th>
                        <th>Damaged (Hz)</th>
                        <th>Repaired (Hz)</th>
                        <th>Recovery (%)</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add modal parameter rows
    for i in range(len(original_freqs)):
        orig = original_freqs[i]
        dmg = damaged_freqs[i]
        rep = repaired_freqs[i]
        
        # Calculate recovery (how close repaired is to original compared to damaged)
        if orig > 0:
            damage_deviation = abs(dmg - orig) / orig * 100
            repair_deviation = abs(rep - orig) / orig * 100
            if damage_deviation > 0:
                recovery = (1 - repair_deviation / damage_deviation) * 100
            else:
                recovery = 100
        else:
            recovery = 0
        
        html_content += f"""
                    <tr>
                        <td><strong>Mode {i+1}</strong></td>
                        <td>{orig:.2f}</td>
                        <td>{dmg:.2f}</td>
                        <td>{rep:.2f}</td>
                        <td><span style="color: {'#76ba1b' if recovery > 50 else '#ff6b6b'}">{recovery:.1f}%</span></td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>📊 Recovery Trajectory</h2>
            <div class="charts-grid full-width">
                <div class="chart-container">
"""
    
    html_content += trajectory_html
    
    html_content += f"""
                </div>
            </div>
        </div>

        <div class="section">
            <h2>💧 Damping Analysis</h2>
            <div class="charts-grid full-width">
                <div class="chart-container">
"""
    
    html_content += damping_html
    
    html_content += f"""
                </div>
            </div>
        </div>

        <div class="section">
            <h2>⚡ Frequency Shift Analysis</h2>
            <div class="charts-grid full-width">
                <div class="chart-container">
"""
    
    html_content += frequency_shift_html
    
    html_content += f"""
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🔋 Modal Energy Distribution</h2>
            <div class="charts-grid full-width">
                <div class="chart-container">
"""
    
    html_content += energy_html
    
    html_content += f"""
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📈 Modal Summary Heatmap</h2>
            <div class="charts-grid full-width">
                <div class="chart-container">
"""
    
    html_content += mode_summary_html
    
    html_content += f"""
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>💡 Detailed Analysis & Recommendations</h2>
            
            <div class="metrics-row">
                <div class="metric-box">
                    <div class="metric-value">{quality_data.get('frequency', 0)*100:.1f}%</div>
                    <div class="metric-label">Frequency Recovery</div>
                    <p style="font-size: 0.85em; color: #888; margin-top: 10px;">
                        How well structural frequencies recovered after repair
                    </p>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{quality_data.get('mode_shape', 0)*100:.1f}%</div>
                    <div class="metric-label">Mode Shape Match</div>
                    <p style="font-size: 0.85em; color: #888; margin-top: 10px;">
                        Similarity of deformation patterns across states
                    </p>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{quality_data.get('damping', 0)*100:.1f}%</div>
                    <div class="metric-label">Damping Recovery</div>
                    <p style="font-size: 0.85em; color: #888; margin-top: 10px;">
                        How well energy dissipation characteristics recovered
                    </p>
                </div>
            </div>
            
            <div class="recommendations">
                <h3>✅ Recommendations & Actions</h3>
                <ul>
                    <li><strong>Overall Assessment:</strong> {interpretation}</li>
                    <li><strong>Next Steps:</strong> Schedule follow-up structural assessment in 6 months</li>
                    <li><strong>Monitoring:</strong> Establish baseline for ongoing vibration monitoring</li>
                    <li><strong>Documentation:</strong> Update maintenance records with repair effectiveness data</li>
                    <li><strong>Focus Areas:</strong> Priority monitoring on modes showing lower recovery rates</li>
                </ul>
            </div>
        </div>
        
        <footer>
            <p>Generated by Structural Repair Quality Analysis System v2.0</p>
            <p class="timestamp">Analysis Date: {analysis_data.get('analysis_date', 'N/A')}</p>
            <p style="margin-top: 10px; font-size: 0.85em; color: #666;">
                This report contains proprietary analysis and should be treated as confidential.
            </p>
        </footer>
    </div>
</body>
</html>
"""
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✓ Enhanced report generated: {output_file}")
    return output_file

if __name__ == "__main__":
    print("Enhanced Report Generator Module")
    print("Use: from enhanced_report_generator import create_enhanced_report")
