// Professional Research Poster - Infrastructure Amnesia Index
// A0 Landscape (1189mm × 841mm) - BALANCED VERSION

#set page(
  width: 1189mm,
  height: 841mm,
  margin: (left: 15mm, right: 15mm, top: 12mm, bottom: 10mm),
  fill: rgb("#f5f5f5")
)

#set text(
  font: "New Computer Modern",
  size: 13pt,
  fill: rgb("#2c3e50")
)

#set par(justify: true, leading: 0.48em, spacing: 0.50em)

// ============================================================================
// HEADER SECTION
// ============================================================================
#align(center)[
  #block(
    fill: gradient.linear(rgb("#1a237e"), rgb("#283593"), rgb("#3949ab")),
    inset: (x: 18pt, y: 10pt),
    radius: 6pt,
    width: 100%,
    stroke: 2pt + rgb("#0d47a1")
  )[
    #text(size: 40pt, fill: white, weight: "bold", tracking: 0.5pt)[
      Infrastructure Amnesia Index
    ]
    #v(2pt)
    #text(size: 22pt, fill: rgb("#bbdefb"), weight: 600)[
      A Novel Approach into Quantifying Repair Efficacy
    ]
    #v(2pt)
    #line(length: 60%, stroke: 1.5pt + rgb("#64b5f6"))
    #v(2pt)
    #text(size: 14pt, fill: rgb("#e3f2fd"), weight: 500)[
      Aayushma Bohora • Bibek Pokhrel • Bighyan Awasthi • Brindal Paudel • Damnee Kumari • Prabesh Kunwar
    ]
    #v(2pt)
    #text(size: 13pt, fill: rgb("#90caf9"), style: "italic")[
      Tribhuvan University, Institute of Engineering, Thapathali Campus
    ]
  ]
]

#v(2pt)

// ============================================================================
// SYSTEM CAPABILITIES BANNER
// ============================================================================
#align(center)[
  #block(
    fill: gradient.linear(rgb("#e8f5e9"), rgb("#c8e6c9")),
    inset: 5pt,
    radius: 5pt,
    stroke: 1.5pt + rgb("#66bb6a"),
    width: 100%
  )[
    #text(size: 13pt, weight: "bold", fill: rgb("#2e7d32"))[
      🎯 System Capabilities: ] 
    #text(size: 13pt, fill: rgb("#1b5e20"))[
      Infrastructure Amnesia Index (IAI) Calculation • Structural Health Monitoring (SHM) • Damage Specification • Damage Localization • Repair Quality Assessment
    ]
  ]
]

#v(2pt)

// ============================================================================
// MAIN CONTENT - 3 Column Grid
// ============================================================================
#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 10pt,
  
  // ═══════════════════════════════════════════════════════════════════════
  // COLUMN 1
  // ═══════════════════════════════════════════════════════════════════════
  [
    // Abstract
    #block(fill: white, inset: 6pt, radius: 5pt, stroke: 1pt + rgb("#e0e0e0"), width: 100%)[
      #align(center)[
        #text(size: 20pt, fill: rgb("#1565c0"), weight: "bold")[📋 ABSTRACT]
        #v(2pt)
        #line(length: 50%, stroke: 2pt + rgb("#42a5f5"))
      ]
      #v(2pt)
      #text(size: 12.5pt)[
        This project developed and validated the *first-of-its-kind index* for quantifying repair efficacy using three main parameters: *Frequency recovery (60%)*, *mode shape preservation (25%)*, and *damping recovery (15%)*. Machine learning models (ANN for baseline identification with 80% confidence, Random Forest for damage specification with 98.28% accuracy) were implemented. Multiple damage scenarios were used to test and validate the index. Observations from the physical model validated the findings of the index to a significant extent.
      ]
    ]
    
    #v(2pt)
    
    // Problem & Objectives
    #block(fill: gradient.linear(rgb("#ffebee"), rgb("#ffcdd2")), inset: 5pt, radius: 5pt, stroke: 1.5pt + rgb("#ef5350"), width: 100%)[
      #text(size: 16pt, fill: rgb("#c62828"), weight: "bold")[⚠️ THE REPAIR VERIFICATION CHALLENGE]
      #v(2pt)
      #text(size: 12pt)[
        *Key Problems:*
        • Current repair assessment relies on subjective visual inspection \
        • No objective, quantitative metrics for repair quality \
        • Safety risks from inadequate repairs \
        • Economic losses from over-repair or repeated interventions
        
        #v(2pt)
        *Objectives:*
        • Develop single repair quality assessment metric applicable to wide range of structures \
        • Develop low-cost accelerometer-based monitoring system \
        • Validate on laboratory scale steel frame
      ]
    ]
    
    #v(2pt)
    
    // Theoretical Framework
    #block(fill: white, inset: 5pt, radius: 5pt, stroke: 1pt + rgb("#e0e0e0"), width: 100%)[
      #align(center)[
        #text(size: 19pt, fill: rgb("#1565c0"), weight: "bold")[⚙️ THEORETICAL FRAMEWORK]
        #v(2pt)
        #line(length: 60%, stroke: 2pt + rgb("#42a5f5"))
      ]
      #v(2pt)
      
      #text(size: 13pt, weight: "bold")[The Composite Quality Score]
      #v(2pt)
      
      #align(center)[
        #block(fill: gradient.linear(rgb("#e3f2fd"), rgb("#bbdefb")), inset: 6pt, radius: 4pt, stroke: 1.5pt + rgb("#1976d2"))[
          #text(size: 15pt, weight: "bold")[
            $Q_"total" = 0.6 dot Q_"freq" + 0.25 dot Q_"shape" + 0.15 dot Q_"damp"$
          ]
        ]
      ]
      
      #v(2pt)
      
      #text(size: 13pt, weight: "bold")[Component Metrics:]
      #v(2pt)
      
      #grid(
        columns: (auto, 1fr),
        row-gutter: 5pt,
        column-gutter: 8pt,
        
        [*1.*], [
          #text(weight: "bold", fill: rgb("#2e7d32"), size: 12.5pt)[Frequency Recovery (60%)]
          $ Q_"freq" = 1 - (f_"rep" - f_"orig") / (f_"dam" - f_"orig") $
          #text(size: 10.5pt)[❑ Most robust indicator \
          ❑ Directly related to stiffness \
          ❑ Literature threshold: 5% detectable change]
        ],
        
        [*2.*], [
          #text(weight: "bold", fill: rgb("#f57c00"), size: 12.5pt)[Mode Shape Preservation (25%)]
          $ Q_"shape" = "MAC"(phi_"orig", phi_"rep") $
          #text(size: 10.5pt)[❑ Spatial damage localization \
          ❑ Modal Assurance Criterion (MAC) \
          ❑ MAC > 0.9: excellent correlation]
        ],
        
        [*3.*], [
          #text(weight: "bold", fill: rgb("#c62828"), size: 12.5pt)[Damping Recovery (15%)]
          $ Q_"damp" = (xi_"rep" - xi_"dam") / (xi_"orig" - xi_"dam") $
          #text(size: 10.5pt)[❑ Sensitive to friction, joint slippage \
          ❑ Hilbert transform estimation \
          ❑ Higher variability but valuable]
        ],
      )
      
      #v(2pt)
      
      #block(fill: rgb("#fff8e1"), inset: 5pt, radius: 3pt)[
        #text(size: 12pt, weight: "bold")[Weighing Scheme Rationale:] 
        #text(size: 10pt)[
          *60% Frequency:* Highest reliability (Salawu, 1997), least noise-sensitive. 
          *25% Mode Shape:* Spatial localization, more noise affected. 
          *15% Damping:* High sensitivity, high uncertainty (30-50% CV).
        ]
      ]
    ]
    
    #v(2pt)
    
    // Mode Shape Chart - SMALLER
    #block(fill: white, inset: 5pt, radius: 5pt, stroke: 1pt + rgb("#e0e0e0"), width: 100%)[
      #align(center)[
        #text(size: 14pt, fill: rgb("#1565c0"), weight: "bold")[Mode Shape Preservation]
      ]
      #v(2pt)
      #image("poster_figures/mode_shape_mac.png", width: 75%)
    ]
  ],
  
  // ═══════════════════════════════════════════════════════════════════════
  // COLUMN 2
  // ═══════════════════════════════════════════════════════════════════════
  [
    // Methodology
    #block(fill: white, inset: 5pt, radius: 5pt, stroke: 1pt + rgb("#e0e0e0"), width: 100%)[
      #align(center)[
        #text(size: 19pt, fill: rgb("#1565c0"), weight: "bold")[🔬 METHODOLOGY]
        #v(2pt)
        #line(length: 50%, stroke: 2pt + rgb("#42a5f5"))
      ]
      #v(2pt)
      
      #text(size: 13pt, weight: "bold")[System Design and Experimental Approach]
      #v(2pt)
      
      #grid(
        columns: (1fr, 1fr),
        gutter: 8pt,
        
        [
          #text(size: 12pt)[
            *Hardware System:*
            • 4 ADXL345 accelerometers \
            • Arduino UNO R3 microcontroller \
            • SD card module and storage \
            • Cables and connectors
            
            #v(2pt)
            
            *Test Structure:*
            • 3 story steel frame \
            • 0.45m × 0.45m × 0.9m \
            • Bolted connection \
            • Fixed base condition \
            • Scale of 1:10
          ]
        ],
        [
          #text(size: 12pt)[
            *Damage Scenarios:*
            • Loose beam-column connection \
            • Missing beams \
            • Deformed structural elements
            
            #v(2pt)
            
            *Repair Methods:*
            • Connection Tightening \
            • Structural element replacement \
            • Diagonal bracing addition
          ]
        ]
      )
    ]
    
    #v(2pt)
    
    // Software Architecture Pipeline
    #block(fill: gradient.linear(rgb("#e8f5e9"), rgb("#c8e6c9")), inset: 5pt, radius: 5pt, stroke: 1.5pt + rgb("#66bb6a"), width: 100%)[
      #text(size: 15pt, fill: rgb("#2e7d32"), weight: "bold")[⚡ SYSTEM IMPLEMENTATION]
      #v(2pt)
      #text(size: 13pt, weight: "bold")[Software Architecture - 9-Step Processing Pipeline:]
      #v(2pt)
      
      #grid(
        columns: (auto, 1fr),
        row-gutter: 3pt,
        column-gutter: 6pt,
        
        [*1.*], [Data Validation (6-point quality check)],
        [*2.*], [Signal Preprocessing (filtering, windowing)],
        [*3.*], [Spectral Analysis (FFT, PSD computation)],
        [*4.*], [Peak Detection (natural frequency extraction)],
        [*5.*], [Mode Shape Estimation (FFT magnitude at peaks)],
        [*6.*], [Damping Estimation (Hilbert transform method)],
        [*7.*], [Mode Matching (Hungarian algorithm)],
        [*8.*], [Quality Metric Computation (weighted scores)],
        [*9.*], [Report Generation (PDF, JSON, Excel, PNG)],
      )
      
      #v(2pt)
      
      #text(size: 12pt)[
        *Key Algorithms:* Welch's method for PSD • Hungarian algorithm for mode matching • Hilbert transform for damping • Savitzky-Golay smoothing
      ]
    ]
    
    #v(2pt)
    
    // Frequency Recovery Chart - SMALLER
    #block(fill: white, inset: 5pt, radius: 5pt, stroke: 1pt + rgb("#e0e0e0"), width: 100%)[
      #align(center)[
        #text(size: 14pt, fill: rgb("#1565c0"), weight: "bold")[Frequency Recovery Analysis]
      ]
      #v(2pt)
      #image("poster_figures/frequency_recovery.png", width: 75%)
    ]
    
    #v(2pt)
    
    // Damping Chart - SMALLER
    #block(fill: white, inset: 5pt, radius: 5pt, stroke: 1pt + rgb("#e0e0e0"), width: 100%)[
      #align(center)[
        #text(size: 14pt, fill: rgb("#1565c0"), weight: "bold")[Damping Recovery Curves]
      ]
      #v(2pt)
      #image("poster_figures/damping_recovery.png", width: 75%)
    ]
    
    #v(2pt)
    
    // ML Models
    #block(fill: gradient.linear(rgb("#e8f5e9"), rgb("#c8e6c9")), inset: 6pt, radius: 4pt, stroke: 1.5pt + rgb("#66bb6a"), width: 100%)[
      #text(size: 13pt, fill: rgb("#1b5e20"), weight: "bold")[🤖 MACHINE LEARNING MODELS]
      #v(2pt)
      #text(size: 12pt)[
        *'No Baseline' Problem:*
        • ANN model for baseline identification \
        • Trained on >1,000,000 data points \
        • Confidence interval: 80%
        
        #v(2pt)
        
        *Damage Specification:*
        • Random Forest Classifier \
        • Trained on >3,000,000 data points \
        • Accuracy: 98.28% \
        • Features used: 69
      ]
    ]
  ],
  
  // ═══════════════════════════════════════════════════════════════════════
  // COLUMN 3
  // ═══════════════════════════════════════════════════════════════════════
  [
    // Results and Analysis
    #block(fill: white, inset: 5pt, radius: 5pt, stroke: 1pt + rgb("#e0e0e0"), width: 100%)[
      #align(center)[
        #text(size: 19pt, fill: rgb("#1565c0"), weight: "bold")[📈 RESULTS AND ANALYSIS]
        #v(2pt)
        #line(length: 60%, stroke: 2pt + rgb("#42a5f5"))
      ]
      #v(2pt)
      
      #text(size: 13pt, weight: "bold")[Experimental Validation Results]
      #v(2pt)
      
      #text(size: 12pt)[
        *Baseline Parameters:*
        • Mode 1: 3.24 ± 0.08 Hz (sway) \
        • Mode 2: 6.18 ± 0.12 Hz \
        • Mode 3: 9.51 ± 0.15 Hz \
        • Damping: 2.5-3.2% (typical for steel)
        
        #v(2pt)
        
        *Damage Detection Performance:*
        • Scenario 2 (loose base): 12.3% frequency reduction ✓ \
        • Scenario 3 (loose joint): 8.7% frequency reduction ✓ \
        • Scenario 5 (combined): 18.2% frequency reduction ✓ \
        • All damage scenarios detected above 5% threshold
        
        #v(2pt)
        
        *Repair Assessment Results:*
      ]
      
      #v(2pt)
      
      #block(fill: rgb("#e8f5e9"), inset: 5pt, radius: 3pt)[
        #text(size: 10.5pt, weight: "bold")[Connection Tightening] \
        #text(size: 10pt)[Frequency recovery: 88-96% • Quality score: 0.82-0.91 • Classification: Good to Very Good]
      ]
      
      #v(2pt)
      
      #block(fill: rgb("#e3f2fd"), inset: 5pt, radius: 3pt)[
        #text(size: 10.5pt, weight: "bold")[Gusset Plate Reinforcement] \
        #text(size: 10pt)[Frequency recovery: 105-125% • Quality score: 0.90-0.98 • Classification: Very Good to Excellent]
      ]
      
      #v(2pt)
      
      #block(fill: rgb("#fff3e0"), inset: 5pt, radius: 3pt)[
        #text(size: 10.5pt, weight: "bold")[Diagonal Bracing] \
        #text(size: 10pt)[Frequency recovery: 140-160% • Quality score: 0.75-0.88 • Classification: Good to Very Good]
      ]
    ]
    
    #v(2pt)
    
    // Validation & Performance
    #block(fill: gradient.linear(rgb("#e8eaf6"), rgb("#c5cae9")), inset: 5pt, radius: 5pt, stroke: 1.5pt + rgb("#5c6bc0"), width: 100%)[
      #text(size: 15pt, fill: rgb("#283593"), weight: "bold")[🏆 VALIDATION AND PERFORMANCE]
      #v(2pt)
      
      #text(size: 13pt, weight: "bold")[Competitive Performance]
      #v(2pt)
      #text(size: 12pt)[
        ✓ Twice as accurate as commercial SHM systems \
        ✓ 30 times cheaper than commercial SHM systems \
        ✓ Faster data processing
      ]
      
      #v(2pt)
      
      #text(size: 12.5pt, weight: "bold")[Success Criteria Met (5/5 ✓)]
      #v(2pt)
      #grid(
        columns: (auto, 1fr, auto),
        row-gutter: 2pt,
        column-gutter: 5pt,
        
        [✓], [Detect ≥5% frequency changes], [*2.5%*],
        [✓], [Damage localization >80% accuracy], [*>80%*],
        [✓], [Quality score correlation R²], [*>0.85*],
        [✓], [Repeatability CV \< 10%], [*2.1-3.8%*],
        [✓], [Complete analysis \<30 minutes], [*\<3 min*],
      )
      
      #v(2pt)
      
      #text(size: 10.5pt)[
        *Statistical Performance:* Repeatability CV \< 10% for frequencies • Detection sensitivity: 2.5% • False positive: 3.2% • False negative: 6.7%
        
        *Uncertainty Quantification:* Frequency ±0.1 Hz • Mode shape MAC ±0.05 • Damping ratio ±0.005 • Overall quality score ±0.08 (95% confidence)
      ]
    ]
    
    #v(2pt)
    
    // Damage Scenarios Chart - SMALLER
    #block(fill: white, inset: 5pt, radius: 5pt, stroke: 1pt + rgb("#e0e0e0"), width: 100%)[
      #align(center)[
        #text(size: 14pt, fill: rgb("#1565c0"), weight: "bold")[Damage Detection Performance]
      ]
      #v(2pt)
      #image("poster_figures/damage_scenarios.png", width: 70%)
    ]
    
    #v(2pt)
    
    // Quality Distribution Chart - SMALLER
    #block(fill: white, inset: 5pt, radius: 5pt, stroke: 1pt + rgb("#e0e0e0"), width: 100%)[
      #align(center)[
        #text(size: 14pt, fill: rgb("#1565c0"), weight: "bold")[Quality Score Distribution]
      ]
      #v(2pt)
      #image("poster_figures/quality_distribution.png", width: 70%)
    ]
  ]
)

#v(2pt)

// ============================================================================
// APPLICATIONS AND CONCLUSIONS - Full Width
// ============================================================================
#grid(
  columns: (1fr, 1fr),
  gutter: 10pt,
  
  [
    #block(fill: gradient.linear(rgb("#fff3e0"), rgb("#ffe0b2")), inset: 5pt, radius: 5pt, stroke: 1.5pt + rgb("#ff9800"), width: 100%)[
      #text(size: 15pt, fill: rgb("#e65100"), weight: "bold")[🌟 APPLICATIONS AND BROADER IMPACTS]
      #v(2pt)
      
      #text(size: 12pt)[
        *Immediate Impacts:*
        • Post-repair verification for bridges and buildings \
        • Seismic retrofit effectiveness assessment \
        • Quality control for repair contractors \
        • Educational tool for structural engineering \
        • Research platform for SHM methodologies
        
        #v(2pt)
        
        *Economic Impacts:*
        • Hardware cost reduction: 30× cheaper \
        • Time savings: 10× faster analysis \
        • Potential savings: 10-30% on repair projects \
        • Democratizes access to advanced SHM technology
        
        #v(2pt)
        
        *Future Developments:*
        • Field validation on full-scale structures \
        • Wireless sensor network implementation \
        • Machine learning for damage classification \
        • Integration with Building Information Modeling (BIM) \
        • Real-time monitoring and alert systems \
        • Standardization and certification pathways
      ]
    ]
  ],
  
  [
    #block(fill: gradient.linear(rgb("#e8f5e9"), rgb("#c8e6c9")), inset: 5pt, radius: 5pt, stroke: 1.5pt + rgb("#66bb6a"), width: 100%)[
      #text(size: 15pt, fill: rgb("#2e7d32"), weight: "bold")[✅ CONCLUSIONS]
      #v(2pt)
      
      #text(size: 12pt)[
        This project successfully developed and validated the *Infrastructure Amnesia Index*, a novel quantitative metric for assessing structural repair efficacy.
        
        #v(2pt)
        
        *Key Achievements:*
        • First-of-its-kind repair quality index \
        • Validated across multiple damage scenarios \
        • 2× more accurate than commercial systems \
        • 30× more cost-effective solution \
        • Successfully integrated ML models (80% and 98.28% accuracy) \
        • 100% validation success rate (60 files tested)
        
        #v(2pt)
        
        *Scientific Contribution:*
        • Establishes objective repair assessment methodology \
        • Provides low-cost alternative to expensive SHM \
        • Demonstrates effectiveness of composite quality scoring \
        • Validates weighing scheme (60%-25%-15%) \
        • Proves viability of ML for baseline-free assessment
        
        #v(2pt)
        
        The system is ready for field deployment and has significant potential to improve structural repair quality control in civil infrastructure.
      ]
    ]
  ]
)

#v(2pt)

// ============================================================================
// REFERENCES - Full Width, Properly Formatted
// ============================================================================
#block(fill: white, inset: 5pt, radius: 5pt, stroke: 1.5pt + rgb("#1565c0"), width: 100%)[
  #text(size: 16pt, fill: rgb("#1565c0"), weight: "bold")[📚 REFERENCES]
  #v(2pt)
  
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 8pt,
    
    [
      #text(size: 9.5pt)[
        [1] Salawu, O. S. (1997). Detection of structural damage through changes in frequency. _Engineering Structures_, 19(9), 718-723.
        
        [2] Allemang, R. J. (2003). The Modal Assurance Criterion - Twenty years of use and abuse. _Sound and Vibration_, 37(8), 14-23.
        
        [3] Farrar, C. R., & Jauregui, D. A. (1998). Comparative study of damage identification algorithms. _Journal of Structural Engineering_, 124(11), 1368-1373.
      ]
    ],
    [
      #text(size: 9.5pt)[
        [4] Feldman, M. (2011). _Hilbert Transform Applications in Mechanical Vibration_. Wiley.
        
        [5] Pandey, A. K., Biswas, M., & Samman, M. M. (1991). Damage detection from changes in curvature mode shapes. _Journal of Sound and Vibration_, 145(2), 321-332.
        
        [6] Pandey, A. K., & Biswas, M. (1994). Damage detection in structures using changes in flexibility. _Journal of Sound and Vibration_, 169(1), 3-17.
      ]
    ],
    [
      #text(size: 9.5pt)[
        [7] Brincker, R., Zhang, L., & Andersen, P. (2001). Modal identification of output-only systems using frequency domain decomposition. _Smart Materials and Structures_, 10(3), 441-445.
        
        [8] Van Overschee, P., & De Moor, B. (1996). _Subspace Identification for Linear Systems: Theory, Implementation and Applications_. Kluwer Academic Publishers.
        
        [9] Doebling, S. W., Farrar, C. R., Prime, M. B., & Shevitz, D. W. (1998). A summary review of vibration-based damage identification methods. _Shock and Vibration Digest_, 30(2), 91-105.
      ]
    ]
  )
]
