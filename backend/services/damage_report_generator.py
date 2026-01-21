"""
Damage Classification Report Generator
Generates comprehensive HTML and PDF reports for AI damage classification results
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np


def create_damage_classification_html_report(
    classification_result: Dict[str, Any],
    file_info: Dict[str, Any],
    output_path: str
) -> str:
    """
    Create comprehensive HTML report for damage classification
    
    Args:
        classification_result: Result from damage classifier
        file_info: Information about uploaded file
        output_path: Path to save HTML report
    
    Returns:
        Path to generated HTML report
    """
    
    # Extract data
    prediction = classification_result['prediction']
    confidence = classification_result['confidence']
    probabilities = classification_result['probabilities']
    top_3 = classification_result['top_3_predictions']
    damage_info = classification_result.get('damage_info', {})
    
    # Get severity color
    severity_colors = {
        'None': '#10b981',
        'Medium': '#f59e0b',
        'High': '#ef4444',
        'Critical': '#991b1b'
    }
    severity = damage_info.get('severity', 'Unknown')
    severity_color = severity_colors.get(severity, '#6b7280')
    
    # Generate probability bars HTML
    prob_bars_html = ""
    sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    for damage_type, prob in sorted_probs:
        bar_width = prob
        bar_color = '#3b82f6' if damage_type == prediction else '#6b7280'
        prob_bars_html += f"""
        <div class="prob-item">
            <div class="prob-label">{damage_type.replace('_', ' ').title()}</div>
            <div class="prob-bar-container">
                <div class="prob-bar" style="width: {bar_width}%; background-color: {bar_color};"></div>
                <div class="prob-value">{prob:.1f}%</div>
            </div>
        </div>
        """
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Damage Classification Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .result-card {{
            background: linear-gradient(135deg, {severity_color} 0%, {severity_color}dd 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .result-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        
        .result-title {{
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .result-confidence {{
            font-size: 3em;
            font-weight: 800;
            margin: 20px 0;
        }}
        
        .result-description {{
            font-size: 1.1em;
            line-height: 1.6;
            margin-bottom: 20px;
            opacity: 0.95;
        }}
        
        .severity-badge {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.3);
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 1.1em;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #1e3a8a;
            margin-bottom: 20px;
            font-weight: 700;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 10px;
        }}
        
        .prob-item {{
            margin-bottom: 15px;
        }}
        
        .prob-label {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #1f2937;
            font-size: 1.1em;
        }}
        
        .prob-bar-container {{
            position: relative;
            background: #e5e7eb;
            height: 40px;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .prob-bar {{
            height: 100%;
            transition: width 0.3s ease;
            border-radius: 8px;
        }}
        
        .prob-value {{
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            font-weight: 700;
            color: #1f2937;
            font-size: 1.1em;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .info-card {{
            background: #f3f4f6;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }}
        
        .info-label {{
            color: #6b7280;
            font-size: 0.9em;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        
        .info-value {{
            color: #1f2937;
            font-size: 1.3em;
            font-weight: 700;
        }}
        
        .recommendation-box {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 25px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        
        .recommendation-title {{
            font-size: 1.3em;
            color: #1e40af;
            font-weight: 700;
            margin-bottom: 15px;
        }}
        
        .recommendation-text {{
            color: #1e3a8a;
            line-height: 1.8;
            font-size: 1.05em;
        }}
        
        .footer {{
            background: #f9fafb;
            padding: 30px;
            text-align: center;
            color: #6b7280;
            border-top: 2px solid #e5e7eb;
        }}
        
        .model-info {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 15px;
        }}
        
        .model-stat {{
            text-align: center;
        }}
        
        .model-stat-value {{
            font-size: 2em;
            font-weight: 700;
            color: #3b82f6;
        }}
        
        .model-stat-label {{
            font-size: 0.9em;
            color: #6b7280;
            margin-top: 5px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 AI Damage Classification Report</h1>
            <div class="subtitle">Structural Health Assessment with Machine Learning</div>
        </div>
        
        <div class="content">
            <!-- Main Result -->
            <div class="result-card">
                <div class="result-icon">{damage_info.get('icon', '🔍')}</div>
                <div class="result-title">{damage_info.get('title', prediction.replace('_', ' ').title())}</div>
                <div class="result-confidence">{confidence:.1f}%</div>
                <div style="font-size: 1.2em; opacity: 0.9; margin-bottom: 10px;">Confidence Level</div>
                <div class="severity-badge">Severity: {severity}</div>
                <div class="result-description">{damage_info.get('description', 'Damage detected.')}</div>
            </div>
            
            <!-- File Information -->
            <div class="section">
                <h2 class="section-title">📄 Analysis Details</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <div class="info-label">File Name</div>
                        <div class="info-value" style="font-size: 1em;">{file_info.get('filename', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Samples Analyzed</div>
                        <div class="info-value">{file_info.get('num_samples', 'N/A'):,}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Sensors</div>
                        <div class="info-value">{file_info.get('num_sensors', 'N/A')}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Duration</div>
                        <div class="info-value">{file_info.get('duration_sec', 0):.1f}s</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Sampling Rate</div>
                        <div class="info-value">{file_info.get('sampling_rate_hz', 100)} Hz</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Analysis Date</div>
                        <div class="info-value" style="font-size: 0.9em;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                    </div>
                </div>
            </div>
            
            <!-- Damage Probabilities -->
            <div class="section">
                <h2 class="section-title">📊 Classification Probabilities</h2>
                {prob_bars_html}
            </div>
            
            <!-- Recommendation -->
            <div class="section">
                <h2 class="section-title">💡 Recommendation</h2>
                <div class="recommendation-box">
                    <div class="recommendation-title">Action Required</div>
                    <div class="recommendation-text">{damage_info.get('recommendation', 'Further inspection recommended.')}</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <div style="font-size: 1.1em; font-weight: 600; color: #1f2937; margin-bottom: 15px;">
                ML Model Performance
            </div>
            <div class="model-info">
                <div class="model-stat">
                    <div class="model-stat-value">98.28%</div>
                    <div class="model-stat-label">Accuracy</div>
                </div>
                <div class="model-stat">
                    <div class="model-stat-value">Random Forest</div>
                    <div class="model-stat-label">Algorithm</div>
                </div>
                <div class="model-stat">
                    <div class="model-stat-value">230</div>
                    <div class="model-stat-label">Training Samples</div>
                </div>
            </div>
            <div style="margin-top: 20px; font-size: 0.9em;">
                Generated by Structural Repair Analysis System • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    # Save HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path


def create_damage_classification_pdf_report(
    classification_result: Dict[str, Any],
    file_info: Dict[str, Any],
    output_path: str
) -> str:
    """
    Create comprehensive PDF report for damage classification
    
    Args:
        classification_result: Result from damage classifier
        file_info: Information about uploaded file
        output_path: Path to save PDF report
    
    Returns:
        Path to generated PDF report
    """
    
    # Extract data
    prediction = classification_result['prediction']
    confidence = classification_result['confidence']
    probabilities = classification_result['probabilities']
    damage_info = classification_result.get('damage_info', {})
    
    with PdfPages(output_path) as pdf:
        # Page 1: Main Result
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        
        # Title
        fig.text(0.5, 0.95, '🔍 AI Damage Classification Report', 
                 ha='center', fontsize=24, fontweight='bold')
        fig.text(0.5, 0.90, 'Structural Health Assessment', 
                 ha='center', fontsize=14, color='gray')
        
        # Main result box
        ax = fig.add_axes([0.15, 0.5, 0.7, 0.35])
        ax.axis('off')
        
        # Severity color
        severity_colors = {
            'None': '#10b981',
            'Medium': '#f59e0b',
            'High': '#ef4444',
            'Critical': '#991b1b'
        }
        severity = damage_info.get('severity', 'Unknown')
        box_color = severity_colors.get(severity, '#6b7280')
        
        rect = mpatches.FancyBboxPatch((0.1, 0.1), 0.8, 0.8, 
                                       boxstyle="round,pad=0.05", 
                                       facecolor=box_color, alpha=0.2, 
                                       edgecolor=box_color, linewidth=3)
        ax.add_patch(rect)
        
        # Result text
        ax.text(0.5, 0.75, damage_info.get('title', prediction.replace('_', ' ').title()),
                ha='center', fontsize=20, fontweight='bold', transform=ax.transAxes)
        ax.text(0.5, 0.55, f"{confidence:.1f}%",
                ha='center', fontsize=36, fontweight='bold', color=box_color, 
                transform=ax.transAxes)
        ax.text(0.5, 0.40, 'Confidence',
                ha='center', fontsize=14, color='gray', transform=ax.transAxes)
        ax.text(0.5, 0.25, f"Severity: {severity}",
                ha='center', fontsize=14, fontweight='bold', transform=ax.transAxes)
        
        # File info
        info_y = 0.40
        fig.text(0.5, info_y, 'Analysis Details', ha='center', fontsize=16, fontweight='bold')
        info_y -= 0.05
        info_text = f"""
File: {file_info.get('filename', 'N/A')}
Samples: {file_info.get('num_samples', 0):,} | Sensors: {file_info.get('num_sensors', 0)} | Duration: {file_info.get('duration_sec', 0):.1f}s
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        fig.text(0.5, info_y-0.08, info_text.strip(), ha='center', fontsize=10, 
                 family='monospace', va='top')
        
        # Recommendation
        fig.text(0.5, 0.15, '💡 Recommendation', ha='center', fontsize=14, fontweight='bold')
        fig.text(0.5, 0.08, damage_info.get('recommendation', 'Further inspection recommended.'),
                 ha='center', fontsize=11, wrap=True, va='top')
        
        # Footer
        fig.text(0.5, 0.02, 'Generated by Structural Repair Analysis System', 
                 ha='center', fontsize=8, color='gray')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Page 2: Probabilities Chart
        fig, ax = plt.subplots(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        
        # Sort probabilities
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        damage_types = [dt.replace('_', ' ').title() for dt, _ in sorted_probs]
        probs = [p for _, p in sorted_probs]
        
        # Create bar chart
        colors = ['#3b82f6' if dt == prediction else '#6b7280' for dt, _ in sorted_probs]
        bars = ax.barh(damage_types, probs, color=colors, edgecolor='black', linewidth=1.5)
        
        # Styling
        ax.set_xlabel('Probability (%)', fontsize=14, fontweight='bold')
        ax.set_title('Classification Probabilities', fontsize=18, fontweight='bold', pad=20)
        ax.set_xlim(0, 100)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Add value labels
        for i, (bar, prob) in enumerate(zip(bars, probs)):
            ax.text(prob + 2, i, f'{prob:.1f}%', va='center', fontweight='bold', fontsize=11)
        
        # Model info
        fig.text(0.5, 0.02, 'Model: Random Forest | Accuracy: 98.28% | Training Samples: 230', 
                 ha='center', fontsize=10, color='gray')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    return output_path
