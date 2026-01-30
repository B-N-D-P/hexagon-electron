// Professional Research Poster - Infrastructure Amnesia Index
// A0 Landscape (1189mm × 841mm)

#set page(
  width: 1189mm,
  height: 841mm,
  margin: (left: 15mm, right: 15mm, top: 12mm, bottom: 12mm),
  fill: rgb("#f5f5f5")
)

#set text(
  font: "New Computer Modern",
  size: 11pt,
  fill: rgb("#2c3e50")
)

#set par(justify: true, leading: 0.48em, spacing: 0.50em)

// ============================================================================
// HEADER SECTION - Professional Banner
// ============================================================================
#align(center)[
  #block(
    fill: gradient.linear(rgb("#1a237e"), rgb("#283593"), rgb("#3949ab")),
    inset: (x: 20pt, y: 12pt),
    radius: 6pt,
    width: 100%,
    stroke: 2pt + rgb("#0d47a1")
  )[
    #text(size: 32pt, fill: white, weight: "bold", tracking: 0.5pt)[
      Infrastructure Amnesia Index
    ]
    #v(2pt)
    #text(size: 18pt, fill: rgb("#bbdefb"), weight: 600)[
      A Novel Approach into Quantifying Repair Efficacy
    ]
    #v(3pt)
    #line(length: 60%, stroke: 1.5pt + rgb("#64b5f6"))
    #v(3pt)
    #text(size: 11pt, fill: rgb("#e3f2fd"), weight: 500)[
      Aayushma Bohora • Bibek Pokhrel • Bighyan Awasthi • Brindal Paudel • Damnee Kumari • Prabesh Kunwar
    ]
    #v(2pt)
    #text(size: 12pt, fill: rgb("#90caf9"), style: "italic")[
      Tribhuvan University, Institute of Engineering, Thapathali Campus
    ]
  ]
]

#v(3pt)

// ============================================================================
// MAIN CONTENT - 3 Column Professional Grid
// ============================================================================
#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 8pt,
  
  // ═══════════════════════════════════════════════════════════════════════
  // COLUMN 1 - Introduction, Theory, Methodology
  // ═══════════════════════════════════════════════════════════════════════
  [
    // Abstract Section
    #block(
      fill: white,
      inset: 6pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 13pt, fill: rgb("#1565c0"), weight: "bold")[📋 ABSTRACT]
        #v(1pt)
        #line(length: 50%, stroke: 2pt + rgb("#42a5f5"))
      ]
      #v(2pt)
      #text(size: 10.5pt)[
        This project developed and validated the *first-of-its-kind index* for quantifying repair efficacy using three main parameters: *Frequency recovery (60%)*, *mode shape preservation (25%)*, and *damping recovery (15%)*. Machine learning models (ANN for baseline identification with 80% confidence, Random Forest for damage specification with 98.28% accuracy) were implemented. Observations from the physical model validated the index across multiple damage scenarios.
      ]
    ]
    
    #v(2pt)
    
    // Problem Statement
    #block(
      fill: gradient.linear(rgb("#ffebee"), rgb("#ffcdd2")),
      inset: 7pt,
      radius: 5pt,
      stroke: 1.5pt + rgb("#ef5350"),
      width: 100%
    )[
      #text(size: 11pt, fill: rgb("#c62828"), weight: "bold")[⚠️ THE CHALLENGE]
      #v(2pt)
      #text(size: 10pt)[
        *Current Problems:*
        • Subjective visual inspections only \
        • No quantitative repair metrics \
        • Safety risks from inadequate repairs \
        • Economic losses from over-repair
        
        #v(2pt)
        *Our Solution:*
        • Single objective quality metric \
        • Low-cost sensor system (30× cheaper) \
        • Validated on laboratory steel frame
      ]
    ]
    
    #v(2pt)
    
    // Theoretical Framework
    #block(
      fill: white,
      inset: 7pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 12pt, fill: rgb("#1565c0"), weight: "bold")[⚙️ COMPOSITE QUALITY SCORE]
        #v(2pt)
        #line(length: 60%, stroke: 2pt + rgb("#42a5f5"))
      ]
      #v(2pt)
      
      #align(center)[
        #block(
          fill: gradient.linear(rgb("#e3f2fd"), rgb("#bbdefb")),
          inset: 7pt,
          radius: 4pt,
          stroke: 1.5pt + rgb("#1976d2")
        )[
          #text(size: 11pt, weight: "bold")[
            $Q_"total" = 0.6 dot Q_"freq" + 0.25 dot Q_"shape" + 0.15 dot Q_"damp"$
          ]
        ]
      ]
      
      #v(3pt)
      
      #grid(
        columns: (auto, 1fr),
        row-gutter: 6pt,
        column-gutter: 8pt,
        
        [*1.*], [
          #text(weight: "bold", fill: rgb("#2e7d32"))[Frequency Recovery (60%)]
          $ Q_"freq" = 1 - (f_"rep" - f_"orig") / (f_"dam" - f_"orig") $
          #text(size: 9.5pt)[Most robust, stiffness-related, 5% threshold]
        ],
        
        [*2.*], [
          #text(weight: "bold", fill: rgb("#f57c00"))[Mode Shape (25%)]
          $ Q_"shape" = "MAC"(phi_"orig", phi_"rep") $
          #text(size: 9.5pt)[Spatial localization, MAC > 0.9 = excellent]
        ],
        
        [*3.*], [
          #text(weight: "bold", fill: rgb("#c62828"))[Damping Recovery (15%)]
          $ Q_"damp" = (xi_"rep" - xi_"dam") / (xi_"orig" - xi_"dam") $
          #text(size: 9.5pt)[Friction/joint slippage, Hilbert transform]
        ],
      )
    ]
    
    #v(2pt)
    
    // Weighing Rationale - Compact Box
    #block(
      fill: rgb("#fff8e1"),
      inset: 6pt,
      radius: 4pt,
      stroke: 1.5pt + rgb("#ffa726"),
      width: 100%
    )[
      #text(size: 12pt, fill: rgb("#e65100"), weight: "bold")[📊 Weighing Rationale]
      #v(3pt)
      #text(size: 9pt)[
        *60% Frequency:* Highest reliability (Salawu, 1997), least noise-sensitive \
        *25% Mode Shape:* Spatial localization, higher noise sensitivity \
        *15% Damping:* Sensitive but high uncertainty (30-50% CV)
      ]
    ]
    
    #v(2pt)
    
    // Mode Shape MAC Chart
    #block(
      fill: white,
      inset: 6pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 11pt, fill: rgb("#1565c0"), weight: "bold")[Mode Shape Preservation]
      ]
      #v(2pt)
      #image("poster_figures/mode_shape_mac.png", width: 100%)
    ]
    
    #v(2pt)
    
    // Damping Recovery Chart
    #block(
      fill: white,
      inset: 6pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 11pt, fill: rgb("#1565c0"), weight: "bold")[Damping Recovery Curves]
      ]
      #v(2pt)
      #image("poster_figures/damping_recovery.png", width: 100%)
    ]
  ],
  
  // ═══════════════════════════════════════════════════════════════════════
  // COLUMN 2 - Methodology, Implementation, Results
  // ═══════════════════════════════════════════════════════════════════════
  [
    // Methodology Section
    #block(
      fill: white,
      inset: 7pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 12pt, fill: rgb("#1565c0"), weight: "bold")[🔬 METHODOLOGY]
        #v(2pt)
        #line(length: 50%, stroke: 2pt + rgb("#42a5f5"))
      ]
      #v(2pt)
      
      #grid(
        columns: (1fr, 1fr),
        gutter: 8pt,
        
        [
          #text(size: 10pt)[
            *Hardware:*
            • 4× ADXL345 sensors \
            • Arduino UNO R3 \
            • SD card storage
            
            *Test Structure:*
            • 3-story steel frame \
            • 0.45m × 0.45m × 0.9m \
            • Bolted, fixed base \
            • Scale 1:10
          ]
        ],
        [
          #text(size: 10pt)[
            *Damage Types:*
            • Loose connections \
            • Missing beams \
            • Deformed elements
            
            *Repair Methods:*
            • Connection tightening \
            • Element replacement \
            • Diagonal bracing
          ]
        ]
      )
    ]
    
    #v(2pt)
    
    // System Pipeline
    #block(
      fill: gradient.linear(rgb("#e8f5e9"), rgb("#c8e6c9")),
      inset: 7pt,
      radius: 5pt,
      stroke: 1.5pt + rgb("#66bb6a"),
      width: 100%
    )[
      #text(size: 11pt, fill: rgb("#2e7d32"), weight: "bold")[⚡ 9-STEP PROCESSING PIPELINE]
      #v(3pt)
      
      #grid(
        columns: (auto, 1fr),
        row-gutter: 3pt,
        column-gutter: 6pt,
        
        [1→], [Data Validation (6-point check)],
        [2→], [Signal Preprocessing],
        [3→], [Spectral Analysis (FFT/PSD)],
        [4→], [Peak Detection],
        [5→], [Mode Shape Estimation],
        [6→], [Damping (Hilbert transform)],
        [7→], [Mode Matching (Hungarian)],
        [8→], [Quality Metric Computation],
        [9→], [Report Generation],
      )
    ]
    
    #v(2pt)
    
    // Frequency Recovery Chart
    #block(
      fill: white,
      inset: 6pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 11pt, fill: rgb("#1565c0"), weight: "bold")[Frequency Recovery Analysis]
      ]
      #v(2pt)
      #image("poster_figures/frequency_recovery.png", width: 100%)
    ]
    
    #v(2pt)
    
    // Damage Scenarios Chart
    #block(
      fill: white,
      inset: 6pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 11pt, fill: rgb("#1565c0"), weight: "bold")[Damage Detection & Repair Effectiveness]
      ]
      #v(2pt)
      #image("poster_figures/damage_scenarios.png", width: 100%)
    ]
    
    #v(2pt)
    
    // ML Models
    #block(
      fill: gradient.linear(rgb("#e8f5e9"), rgb("#c8e6c9")),
      inset: 6pt,
      radius: 4pt,
      stroke: 1.5pt + rgb("#66bb6a"),
      width: 100%
    )[
      #text(size: 12pt, fill: rgb("#1b5e20"), weight: "bold")[🤖 MACHINE LEARNING MODELS]
      #v(2pt)
      #text(size: 9.5pt)[
        *Baseline Identification:* ANN • >1M data points • 80% confidence \
        *Damage Specification:* Random Forest • >3M points • 98.28% accuracy • 69 features
      ]
    ]
  ],
  
  // ═══════════════════════════════════════════════════════════════════════
  // COLUMN 3 - Results, Validation, Impact
  // ═══════════════════════════════════════════════════════════════════════
  [
    // Experimental Results
    #block(
      fill: white,
      inset: 7pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 12pt, fill: rgb("#1565c0"), weight: "bold")[📈 EXPERIMENTAL RESULTS]
        #v(2pt)
        #line(length: 60%, stroke: 2pt + rgb("#42a5f5"))
      ]
      #v(2pt)
      
      #text(size: 10pt)[
        *Baseline Parameters:*
        • Mode 1: 3.24±0.08 Hz (sway) \
        • Mode 2: 6.18±0.12 Hz \
        • Mode 3: 9.51±0.15 Hz \
        • Damping: 2.5-3.2% (steel)
        
        #v(2pt)
        
        *Damage Detection:*
        • Loose base: 12.3% ↓ ✓ \
        • Loose joint: 8.7% ↓ ✓ \
        • Combined: 18.2% ↓ ✓ \
        • All > 5% threshold
      ]
      
      #v(2pt)
      
      #block(fill: rgb("#e8f5e9"), inset: 6pt, radius: 3pt)[
        #text(size: 9.5pt, weight: "bold")[Connection Tightening] \
        #text(size: 9pt)[Recovery: 88-96% • Score: 0.82-0.91 • Good to Very Good]
      ]
      
      #v(3pt)
      
      #block(fill: rgb("#e3f2fd"), inset: 6pt, radius: 3pt)[
        #text(size: 9.5pt, weight: "bold")[Gusset Plate Reinforcement] \
        #text(size: 9pt)[Recovery: 105-125% • Score: 0.90-0.98 • Very Good to Excellent]
      ]
      
      #v(3pt)
      
      #block(fill: rgb("#fff3e0"), inset: 6pt, radius: 3pt)[
        #text(size: 9.5pt, weight: "bold")[Diagonal Bracing] \
        #text(size: 9pt)[Recovery: 140-160% • Score: 0.75-0.88 • Good to Very Good]
      ]
    ]
    
    #v(2pt)
    
    // Performance Comparison
    #block(
      fill: gradient.linear(rgb("#e8eaf6"), rgb("#c5cae9")),
      inset: 7pt,
      radius: 5pt,
      stroke: 1.5pt + rgb("#5c6bc0"),
      width: 100%
    )[
      #text(size: 11pt, fill: rgb("#283593"), weight: "bold")[🏆 COMPETITIVE PERFORMANCE]
      #v(3pt)
      
      #text(size: 10pt)[
        *vs Commercial SHM Systems:* \
        ✓ *2× more accurate* detection \
        ✓ *30× cheaper* hardware cost \
        ✓ *10× faster* data processing
      ]
      
      #v(2pt)
      
      #text(size: 10pt, weight: "bold")[Success Criteria (5/5 ✓)]
      #grid(
        columns: (auto, 1fr, auto),
        row-gutter: 2pt,
        column-gutter: 4pt,
        
        [✓], [Frequency detection], [*2.5%* (target: ≥5%)],
        [✓], [Localization], [*>80%* accuracy],
        [✓], [Score correlation], [*R² > 0.85*],
        [✓], [Repeatability], [*CV: 2.1-3.8%*],
        [✓], [Analysis time], [*\<3 min* (target: \<30)],
      )
      
      #v(2pt)
      
      #text(size: 9pt)[
        *Statistics:* Sensitivity 2.5% • FPR 3.2% • FNR 6.7% \
        *Uncertainty:* Freq ±0.1Hz • MAC ±0.05 • Damp ±0.005
      ]
    ]
    
    #v(2pt)
    
    // Quality Distribution Chart
    #block(
      fill: white,
      inset: 6pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 11pt, fill: rgb("#1565c0"), weight: "bold")[Quality Score Distribution]
      ]
      #v(2pt)
      #image("poster_figures/quality_distribution.png", width: 100%)
    ]
    
    #v(2pt)
    
    // Performance Metrics Chart
    #block(
      fill: white,
      inset: 6pt,
      radius: 5pt,
      stroke: 1pt + rgb("#e0e0e0"),
      width: 100%
    )[
      #align(center)[
        #text(size: 11pt, fill: rgb("#1565c0"), weight: "bold")[System Performance Validation]
      ]
      #v(2pt)
      #image("poster_figures/performance_metrics.png", width: 100%)
    ]
    
    #v(2pt)
    
    // Impact & Future Work
    #block(
      fill: gradient.linear(rgb("#fff3e0"), rgb("#ffe0b2")),
      inset: 6pt,
      radius: 4pt,
      stroke: 1.5pt + rgb("#ff9800"),
      width: 100%
    )[
      #text(size: 12pt, fill: rgb("#e65100"), weight: "bold")[🌟 IMPACT & FUTURE]
      #v(2pt)
      #text(size: 9pt)[
        *Applications:* Post-repair verification • Seismic retrofit • Quality control • Education
        
        *Economics:* 30× cheaper • 10× faster • 10-30% project savings
        
        *Future:* Field validation • Wireless networks • BIM integration • Real-time monitoring
      ]
    ]
  ]
)

#v(3pt)

// ============================================================================
// FOOTER - Compact References
// ============================================================================
#align(center)[
  #block(
    fill: white,
    inset: 6pt,
    radius: 4pt,
    stroke: 1pt + rgb("#bdbdbd"),
    width: 100%
  )[
    #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[📚 References: ]
    #text(size: 8pt)[
      Salawu (1997) Eng. Struct. 19(9):718-723 • Allemang (2003) Sound Vib. 37(8):14-23 • Farrar & Jauregui (1998) J. Struct. Eng. 124(11):1368-1373 • Feldman (2011) Wiley • Pandey et al. (1991, 1994) J. Sound Vib. • Brincker et al. (2001) Smart Mater. Struct. 10(3):441-445 • Brownjohn (2007) Phil. Trans. Royal Soc. 365(1851):589-622
    ]
  ]
]
