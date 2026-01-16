#!/usr/bin/env python3
"""
Enhanced PDF Report Generator
Includes ALL graphs and visualizations for comprehensive analysis
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.gridspec import GridSpec
import numpy as np
from datetime import datetime

def create_comprehensive_pdf_report(modal_params_list, quality_data, enhanced_graphs, 
                                    output_path="comprehensive_report.pdf"):
    """
    Create a comprehensive PDF report with ALL graphs and visualizations
    """
    
    pdf_path = output_path
    
    with PdfPages(pdf_path) as pdf:
        # PAGE 1: Title Page with Executive Summary
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('#0a0e27')
        gs = fig.add_gridspec(4, 1, height_ratios=[1, 1.5, 1.5, 0.5], hspace=0.4)
        
        # Title
        ax_title = fig.add_subplot(gs[0])
        ax_title.axis('off')
        title_text = "STRUCTURAL REPAIR QUALITY ANALYSIS\nComprehensive Report"
        ax_title.text(0.5, 0.5, title_text, fontsize=26, fontweight='bold', 
                ha='center', va='center', color='#66feff', 
                bbox=dict(boxstyle='round', facecolor='#0f3460', edgecolor='#66feff', linewidth=3, pad=1))
        
        # Quality Overview
        ax_qual = fig.add_subplot(gs[1])
        ax_qual.axis('off')
        quality = quality_data
        overall_score = quality.get('overall', 0)*100
        
        # Color based on quality
        if overall_score >= 80:
            score_color = '#4caf50'  # Green
            interp = "EXCELLENT"
        elif overall_score >= 60:
            score_color = '#ffc107'  # Yellow
            interp = "GOOD"
        elif overall_score >= 40:
            score_color = '#ff9800'  # Orange
            interp = "FAIR"
        else:
            score_color = '#ff6b6b'  # Red
            interp = "POOR"
        
        score_display = f"{overall_score:.1f}%"
        ax_qual.text(0.5, 0.7, score_display, fontsize=48, fontweight='bold',
                ha='center', va='center', color=score_color)
        ax_qual.text(0.5, 0.3, f"Overall Quality - {interp}\n{quality.get('interpretation', 'N/A')}", 
                fontsize=14, ha='center', va='center', color='#e0e6ed',
                bbox=dict(boxstyle='round', facecolor='#16213e', alpha=0.7, pad=0.8))
        
        # Quality Breakdown Details
        ax_breakdown = fig.add_subplot(gs[2])
        ax_breakdown.axis('off')
        breakdown_text = f"""
QUALITY BREAKDOWN:

Frequency Recovery .......................... {quality.get('frequency', 0)*100:.1f}%
  Measures how well structural frequencies recovered after repair

Mode Shape Match ............................ {quality.get('mode_shape', 0)*100:.1f}%
  Measures similarity of deformation patterns across states

Damping Recovery ............................ {quality.get('damping', 0)*100:.1f}%
  Measures how well energy dissipation characteristics recovered

OVERALL ASSESSMENT: {quality.get('interpretation', 'N/A')}
        """
        ax_breakdown.text(0.05, 0.5, breakdown_text, fontsize=11, ha='left', va='center',
                color='#e0e6ed', family='monospace',
                bbox=dict(boxstyle='round', facecolor='#16213e', alpha=0.8, pad=1))
        
        # Footer
        ax_footer = fig.add_subplot(gs[3])
        ax_footer.axis('off')
        ax_footer.text(0.5, 0.5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                fontsize=10, ha='center', va='center', color='#a0a0a0')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
        # PAGE 2: Modal Parameters
        if modal_params_list and len(modal_params_list) >= 3:
            fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
            fig.patch.set_facecolor('#0a0e27')
            
            modal_orig, modal_dmg, modal_rep = modal_params_list[0], modal_params_list[1], modal_params_list[2]
            modes = range(1, min(len(modal_orig.frequencies), 6))
            
            # Frequencies
            ax = axes[0, 0]
            x = np.arange(len(modes))
            width = 0.25
            ax.bar(x - width, [modal_orig.frequencies[i] for i in modes], width, label='Original', color='#00d9ff')
            ax.bar(x, [modal_dmg.frequencies[i] for i in modes], width, label='Damaged', color='#ff6b6b')
            ax.bar(x + width, [modal_rep.frequencies[i] for i in modes], width, label='Repaired', color='#4caf50')
            ax.set_xlabel('Mode', color='#e0e6ed')
            ax.set_ylabel('Frequency (Hz)', color='#e0e6ed')
            ax.set_title('Natural Frequencies', color='#66feff', fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels([f'M{i+1}' for i in modes])
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#16213e')
            ax.tick_params(colors='#e0e6ed')
            
            # Damping Ratios
            ax = axes[0, 1]
            ax.bar(x - width, [modal_orig.damping[i]*100 for i in modes], width, label='Original', color='#00d9ff')
            ax.bar(x, [modal_dmg.damping[i]*100 for i in modes], width, label='Damaged', color='#ff6b6b')
            ax.bar(x + width, [modal_rep.damping[i]*100 for i in modes], width, label='Repaired', color='#4caf50')
            ax.set_xlabel('Mode', color='#e0e6ed')
            ax.set_ylabel('Damping Ratio (%)', color='#e0e6ed')
            ax.set_title('Damping Ratios', color='#66feff', fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels([f'M{i+1}' for i in modes])
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#16213e')
            ax.tick_params(colors='#e0e6ed')
            
            # Frequency Shift (Damage)
            ax = axes[1, 0]
            freq_shifts_dmg = [(modal_dmg.frequencies[i] - modal_orig.frequencies[i])/modal_orig.frequencies[i]*100 
                               for i in modes]
            colors_dmg = ['#ff6b6b' if x < 0 else '#ffd93d' for x in freq_shifts_dmg]
            ax.bar(modes, freq_shifts_dmg, color=colors_dmg, edgecolor='#e0e6ed', linewidth=1.5)
            ax.axhline(y=0, color='#66feff', linestyle='--', linewidth=1)
            ax.set_xlabel('Mode', color='#e0e6ed')
            ax.set_ylabel('Frequency Shift (%)', color='#e0e6ed')
            ax.set_title('Frequency Change: Damaged vs Original', color='#66feff', fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_facecolor('#16213e')
            ax.tick_params(colors='#e0e6ed')
            
            # Frequency Recovery (Repaired)
            ax = axes[1, 1]
            freq_shifts_rep = [(modal_rep.frequencies[i] - modal_orig.frequencies[i])/modal_orig.frequencies[i]*100 
                               for i in modes]
            colors_rep = ['#4caf50' if abs(x) < abs(freq_shifts_dmg[j]) else '#ff6b6b' 
                          for j, x in enumerate(freq_shifts_rep)]
            ax.bar(modes, freq_shifts_rep, color=colors_rep, edgecolor='#e0e6ed', linewidth=1.5)
            ax.axhline(y=0, color='#66feff', linestyle='--', linewidth=1)
            ax.set_xlabel('Mode', color='#e0e6ed')
            ax.set_ylabel('Frequency Shift (%)', color='#e0e6ed')
            ax.set_title('Frequency Recovery: Repaired vs Original', color='#66feff', fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_facecolor('#16213e')
            ax.tick_params(colors='#e0e6ed')
            
            fig.suptitle('Modal Parameters Analysis', fontsize=16, fontweight='bold', color='#66feff')
            fig.patch.set_facecolor('#0a0e27')
            
            for ax in axes.flat:
                ax.spines['bottom'].set_color('#a0a0a0')
                ax.spines['left'].set_color('#a0a0a0')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
        
        # PAGE 3: Enhanced Graphs - Damping & Quality
        if 'damping_comparison' in enhanced_graphs:
            fig, axes = plt.subplots(2, 1, figsize=(11, 8.5))
            fig.patch.set_facecolor('#0a0e27')
            
            damping_data = enhanced_graphs['damping_comparison'].get('damping_data', [])
            damping_quality = enhanced_graphs['damping_comparison'].get('damping_fit_quality', [])
            
            if damping_data:
                # Damping Ratio Comparison
                ax = axes[0]
                modes_names = [d['mode'] for d in damping_data]
                orig_vals = [d.get('original', 0)*100 for d in damping_data]
                dmg_vals = [d.get('damaged', 0)*100 for d in damping_data]
                rep_vals = [d.get('repaired', 0)*100 for d in damping_data]
                
                x = np.arange(len(modes_names))
                width = 0.25
                ax.bar(x - width, orig_vals, width, label='Original', color='#00d9ff')
                ax.bar(x, dmg_vals, width, label='Damaged', color='#ff6b6b')
                ax.bar(x + width, rep_vals, width, label='Repaired', color='#4caf50')
                ax.set_ylabel('Damping Ratio (%)', color='#e0e6ed')
                ax.set_title('Damping Ratio Comparison (%)', color='#66feff', fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(modes_names)
                ax.legend()
                ax.grid(True, alpha=0.3, axis='y')
                ax.set_facecolor('#16213e')
                ax.tick_params(colors='#e0e6ed')
                
                # Damping Fit Quality (R²)
                ax = axes[1]
                orig_r2 = [d.get('original', 0.85) for d in damping_quality]
                dmg_r2 = [d.get('damaged', 0.85) for d in damping_quality]
                rep_r2 = [d.get('repaired', 0.85) for d in damping_quality]
                
                ax.bar(x - width, orig_r2, width, label='Original', color='#00d9ff')
                ax.bar(x, dmg_r2, width, label='Damaged', color='#ff6b6b')
                ax.bar(x + width, rep_r2, width, label='Repaired', color='#4caf50')
                ax.set_ylabel('R² (Fit Quality)', color='#e0e6ed')
                ax.set_title('Damping Fit Quality (R²)', color='#66feff', fontweight='bold')
                ax.set_ylim([0.8, 1.0])
                ax.set_xticks(x)
                ax.set_xticklabels(modes_names)
                ax.legend()
                ax.grid(True, alpha=0.3, axis='y')
                ax.set_facecolor('#16213e')
                ax.tick_params(colors='#e0e6ed')
                
                for ax in axes:
                    ax.spines['bottom'].set_color('#a0a0a0')
                    ax.spines['left'].set_color('#a0a0a0')
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                
                fig.suptitle('Damping Analysis', fontsize=16, fontweight='bold', color='#66feff')
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
        
        # PAGE 4: Energy & Mode Information
        if 'energy_distribution' in enhanced_graphs:
            fig, axes = plt.subplots(1, 2, figsize=(11, 8.5))
            fig.patch.set_facecolor('#0a0e27')
            
            energy_data = enhanced_graphs.get('energy_distribution', {})
            
            if 'original_energy' in energy_data:
                # Energy Distribution
                ax = axes[0]
                modes = list(range(1, 6))
                orig_energy = energy_data.get('original_energy', [0]*5)[:5]
                
                ax.bar(modes, orig_energy, color='#00d9ff', edgecolor='#e0e6ed', linewidth=1.5)
                ax.set_xlabel('Mode', color='#e0e6ed')
                ax.set_ylabel('Energy Distribution (%)', color='#e0e6ed')
                ax.set_title('Energy Distribution (Original)', color='#66feff', fontweight='bold')
                ax.set_xticks(modes)
                ax.grid(True, alpha=0.3, axis='y')
                ax.set_facecolor('#16213e')
                ax.tick_params(colors='#e0e6ed')
            
            # Quality Breakdown
            ax = axes[1]
            labels = ['Frequency\nRecovery', 'Mode Shape\nMatch', 'Damping\nRecovery']
            sizes = [
                quality.get('frequency', 0)*100,
                quality.get('mode_shape', 0)*100,
                quality.get('damping', 0)*100
            ]
            colors = ['#ffc107', '#4caf50', '#00d9ff']
            explode = (0.05, 0.05, 0.05)
            
            ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                   shadow=True, startangle=90, textprops={'color': '#e0e6ed'})
            ax.set_title('Quality Breakdown', color='#66feff', fontweight='bold')
            
            for ax in axes:
                ax.spines['bottom'].set_color('#a0a0a0')
                ax.spines['left'].set_color('#a0a0a0')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
            
            fig.suptitle('Energy & Quality Analysis', fontsize=16, fontweight='bold', color='#66feff')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
    
    print(f"✓ Comprehensive PDF report generated: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    print("Enhanced PDF Generator Module")
    print("Use: from enhanced_pdf_generator import create_comprehensive_pdf_report")
