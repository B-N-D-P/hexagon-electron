// Infrastructure Amnesia Index Research Poster
// A0 Size (841mm x 1189mm)

#set page(
  width: 1189mm,
  height: 841mm,
  margin: (left: 12mm, right: 12mm, top: 10mm, bottom: 10mm),
  fill: rgb("#f8f9fa")
)

#set text(
  font: "New Computer Modern",
  size: 10pt,
  fill: rgb("#212529")
)

#set par(justify: true, leading: 0.45em)

// Title Section
#align(center)[
  #block(fill: rgb("#0d47a1"), inset: 10pt, radius: 4pt, width: 85%)[
    #text(size: 32pt, fill: white, weight: "bold")[
      Infrastructure Amnesia Index: A Novel Approach into Quantifying Repair Efficacy
    ]
    
    #v(2pt)
    
    #text(size: 10pt, fill: rgb("#bbdefb"))[
      Aayushma Bohora, Bibek Pokhrel, Bighyan Awasthi, Brindal Paudel, Damnee Kumari, Prabesh Kunwar
    ]
    
    #v(2pt)
    
    #text(size: 10pt, fill: rgb("#e3f2fd"))[
      Tribhuvan University, Institute of Engineering, Thapathali Campus
    ]
  ]
]

#v(3pt)

// Three Column Layout
#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 6pt,
  
  // ========== COLUMN 1 ==========
  [
    // Abstract Box
    #block(fill: white, inset: 5pt, radius: 3pt, stroke: rgb("#dee2e6"))[
      #text(size: 10pt, fill: rgb("#0d47a1"), weight: "bold")[Abstract]
      #v(3pt)
      #text(size: 10pt)[
        This project developed and validated an index for quantifying repair efficacy, which is the first of its kind. The index utilizes three main parameters derived primarily from acceleration data: *Frequency recovery* (60%), *mode shape preservation* (25%), and *damping recovery* (15%). Multiple damage scenarios were used to test and validate the index. A machine learning model based on Artificial Neural Network was implemented for cases where baseline data might not be available. Another model based on random forest classifier was trained for damage specification. The model for baseline identification, trained on data from the physical structure, gave a confidence interval of 80%. The observations from the physical model validated the findings of the index to a significant extent.
      ]
    ]
    
    #v(2pt)
    
    // Introduction Box
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 12pt, fill: rgb("#0d47a1"), weight: "bold")[Introduction]
      #v(3pt)
      
      #text(size: 10pt, fill: rgb("#d32f2f"), weight: "bold")[The Repair Verification Challenge]
      #v(3pt)
      
      #text(size: 10pt)[
        *Key Problems:*
        - Current structural repair assessment relies on subjective visual inspection
        - No objective, quantitative metrics for repair quality
        - Safety risks from inadequate repairs
        - Economic losses from over-repair or repeated interventions
        
        #v(3pt)
        *Objectives:*
        - Develop a single repair quality assessment metric applicable to a wide range of structures
        - Develop a low-cost accelerometer-based monitoring system
        - Validate on a laboratory scale steel frame
      ]
    ]
    
    #v(2pt)
    
    // Theoretical Framework Box
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 12pt, fill: rgb("#0d47a1"), weight: "bold")[Theoretical Framework]
      #v(3pt)
      
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[The Composite Quality Score]
      #v(3pt)
      
      #align(center)[
        #block(fill: rgb("#e3f2fd"), inset: 10pt, radius: 3pt)[
          #text(size: 10pt, weight: "bold")[
            $Q_"total" = 0.6 times Q_"freq" + 0.25 times Q_"shape" + 0.15 times Q_"damp"$
          ]
        ]
      ]
      
      #v(3pt)
      
      #text(size: 10pt, weight: "bold")[Component Metrics:]
      #v(3pt)
      
      #text(size: 10pt)[
        *1. Frequency Recovery (60%)*
        
        $ Q_"freq" = 1 - (f_"rep" - f_"orig") / (f_"dam" - f_"orig") $
        
        - Most robust indicator
        - Directly related to stiffness
        - Literature threshold: 5% detectable change
        
        #v(3pt)
        
        *2. Mode Shape Preservation (25%)*
        
        $ Q_"shape" = "MAC"(phi_"orig", phi_"rep") $
        
        - Spatial damage localization
        - Modal Assurance Criterion (MAC)
        - MAC > 0.9: excellent correlation
        
        #v(3pt)
        
        *3. Damping Recovery (15%)*
        
        $ Q_"damp" = (xi_"rep" - xi_"dam") / (xi_"orig" - xi_"dam") $
        
        - Sensitive to friction, joint slippage
        - Hilbert transform estimation
        - Higher variability but valuable
      ]
    ]
    
    #v(2pt)
    
    // Weighing Scheme Box
    #block(fill: rgb("#fff3e0"), inset: 4pt, radius: 3pt, stroke: rgb("#ff9800"))[
      #text(size: 10pt, fill: rgb("#e65100"), weight: "bold")[Weighing Scheme Rationale]
      #v(2pt)
      #text(size: 10pt)[
        *Frequency (60%):* Highest reliability, least noise sensitive, direct stiffness relationship.
        *Mode Shape (25%):* Spatial localization, more noise affected.
        *Damping (15%):* High sensitivity, high uncertainty (30-50% CV).
      ]
    ]
    
    #v(2pt)
    
    // Graph - Mode Shape MAC
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[Mode Shape Preservation]
      #v(3pt)
      
      #align(center)[
        #image("poster_figures/mode_shape_mac.png", width: 85%)
      ]
    ]
    
    #v(2pt)
    
    // Graph - Damping Recovery
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[Damping Recovery]
      #v(3pt)
      
      #align(center)[
        #image("poster_figures/damping_recovery.png", width: 85%)
      ]
    ]
  ],
  
  // ========== COLUMN 2 ==========
  [
    // Methodology Box
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 12pt, fill: rgb("#0d47a1"), weight: "bold")[Methodology]
      #v(3pt)
      
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[System Design and Experimental Approach]
      #v(3pt)
      
      #grid(
        columns: (1fr, 1fr),
        gutter: 6pt,
        
        [
          #text(size: 10pt)[
            *Hardware System:*
            - 4 ADXL345 accelerometers
            - Arduino UNO R3 microcontroller
            - SD card module and storage
            
            
            #v(2pt)
            
            *Test Structure:*
            - 3 story steel frame
            - 0.45m × 0.45m × 0.9m
            - Bolted connection
            
            - Fixed base, Scale 1:10
          ]
        ],
        [
          #text(size: 10pt)[
            *Damage Scenarios:*
            - Loose beam-column connection
            - Missing beams
            - Deformed elements
            
            
            
            *Repair Methods:*
            - Connection Tightening
            - Element replacement
            - Diagonal bracing addition
          ]
        ]
      )
    ]
    
    #v(2pt)
    
    // System Implementation Box
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 12pt, fill: rgb("#0d47a1"), weight: "bold")[System Implementation]
      #v(3pt)
      
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[Software Architecture]
      #v(3pt)
      
      #text(size: 10pt)[
        *9-step processing pipeline:*
        
        #grid(
          columns: (auto, 1fr),
          row-gutter: 4pt,
          column-gutter: 8pt,
          
          [1.], [Data Validation (6-point quality check)],
          [2.], [Signal Preprocessing (filtering, windowing)],
          [3.], [Spectral Analysis (FFT, PSD computation)],
          [4.], [Peak Detection (natural frequency extraction)],
          [5.], [Mode Shape Estimation (FFT magnitude at peaks)],
          [6.], [Damping Estimation (Hilbert transform method)],
          [7.], [Mode Matching (Hungarian algorithm)],
          [8.], [Quality Metric Computation (weighted scores)],
          [9.], [Report Generation (PDF, JSON, Excel, PNG)],
        )
      ]
    ]
    
    #v(2pt)
    
    // Graph 1 - Frequency Recovery
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[Frequency Recovery Analysis]
      #v(3pt)
      
      #align(center)[
        #image("poster_figures/frequency_recovery.png", width: 85%)
      ]
    ]
    
    #v(2pt)
    
    // Graph 2 - Damage Scenarios
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[Damage Detection & Repair]
      #v(3pt)
      
      #align(center)[
        #image("poster_figures/damage_scenarios.png", width: 85%)
      ]
    ]
    
    #v(2pt)
    
    // Machine Learning Models Box
    #block(fill: rgb("#e8f5e9"), inset: 4pt, radius: 3pt, stroke: rgb("#4caf50"))[
      #text(size: 10pt, fill: rgb("#1b5e20"), weight: "bold")[Machine Learning Models]
      #v(2pt)
      
      #text(size: 10pt)[
        *'No Baseline' Problem:* ANN model, >1M data points, 80% confidence
        
        *Damage Specification:* Random Forest, >3M points, 98.28% accuracy, 69 features
      ]
    ]
  ],
  
  // ========== COLUMN 3 ==========
  [
    // Results and Analysis Box
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 12pt, fill: rgb("#0d47a1"), weight: "bold")[Results and Analysis]
      #v(3pt)
      
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[Experimental Validation Results]
      #v(3pt)
      
      #text(size: 10pt)[
        *Baseline Parameters:*
        - Mode 1: 3.24 ± 0.08 Hz (sway)
        - Mode 2: 6.18 ± 0.12 Hz
        - Mode 3: 9.51 ± 0.15 Hz
        - Damping: 2.5-3.2% (typical for steel)
        
        #v(3pt)
        
        *Damage Detection Performance:*
        - Scenario 2 (loose base): 12.3% frequency reduction ✓
        - Scenario 3 (loose joint): 8.7% frequency reduction ✓
        - Scenario 5 (combined): 18.2% frequency reduction ✓
        - All damage scenarios detected above 5% threshold
        
        #v(3pt)
        
        *Repair Assessment Results:*
        
        #block(fill: rgb("#e8f5e9"), inset: 5pt, radius: 3pt)[
          *Connection Tightening:*
          - Frequency recovery: 88-96%
          - Quality score: 0.82-0.91
          - Classification: Good to Very Good
        ]
        
        #v(3pt)
        
        #block(fill: rgb("#e3f2fd"), inset: 5pt, radius: 3pt)[
          *Gusset Plate Reinforcement:*
          - Frequency recovery: 105-125%
          - Quality score: 0.90-0.98
          - Classification: Very Good to Excellent
        ]
        
        #v(3pt)
        
        #block(fill: rgb("#fff3e0"), inset: 5pt, radius: 3pt)[
          *Diagonal Bracing:*
          - Frequency recovery: 140-160%
          - Quality score: 0.75-0.88
          - Classification: Good to Very Good
        ]
      ]
    ]
    
    #v(2pt)
    
    // Validation Performance Box
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 12pt, fill: rgb("#0d47a1"), weight: "bold")[Validation and Performance]
      #v(3pt)
      
      #text(size: 10pt)[
        *Competitive Performance:*
        - 2× more accurate than commercial SHM systems
        - 30× cheaper than commercial SHM systems
        - Faster data processing
        
        #v(3pt)
        
        *Success Criteria Met:*
        
        #grid(
          columns: (auto, 1fr, auto),
          row-gutter: 4pt,
          column-gutter: 6pt,
          
          [✓], [Detect ≥5% frequency changes], [*2.5%*],
          [✓], [Damage localization accuracy], [*>80%*],
          [✓], [Quality score correlation R²], [*>0.85*],
          [✓], [Repeatability CV], [*2.1-3.8%*],
          [✓], [Analysis time \<30 min], [*\<3 min*],
        )
        
        #v(3pt)
        
        *Statistical Performance:*
        - Repeatability: CV < 10%, Detection: 2.5%, False positive: 3.2%, False negative: 6.7%
        
        *Uncertainty:* Frequency ±0.1 Hz, MAC ±0.05, Damping ±0.005, Score ±0.08 (95% CI)
      ]
    ]
    
    #v(2pt)
    
    // Graph 3 - Quality Score Distribution
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[Quality Score Distribution]
      #v(3pt)
      
      #align(center)[
        #image("poster_figures/quality_distribution.png", width: 85%)
      ]
    ]
    
    #v(2pt)
    
    // Graph 4 - Performance Metrics
    #block(fill: white, inset: 5pt, radius: 4pt, stroke: rgb("#dee2e6"))[
      #text(size: 10pt, fill: rgb("#1565c0"), weight: "bold")[System Performance]
      #v(3pt)
      
      #align(center)[
        #image("poster_figures/performance_metrics.png", width: 85%)
      ]
    ]
    
    #v(2pt)
    
    // Applications Box
    #block(fill: white, inset: 4pt, radius: 3pt, stroke: rgb("#dee2e6"))[
      #text(size: 13pt, fill: rgb("#0d47a1"), weight: "bold")[Applications & Future Work]
      #v(2pt)
      
      #text(size: 10pt)[
        *Immediate Impacts:* Post-repair verification, seismic retrofit assessment, quality control, educational tool
        
        *Economic Impacts:* 30× cheaper, 10× faster, 10-30% savings on projects
        
        *Future:* Field validation, wireless networks, BIM integration, real-time monitoring
      ]
    ]
  ]
)

#v(2pt)

// References - Compact
#align(center)[
  #block(fill: white, inset: 3pt, radius: 2pt, stroke: rgb("#dee2e6"), width: 100%)[
    #text(size: 9pt, fill: rgb("#0d47a1"), weight: "bold")[References: ] 
    #text(size: 7pt)[Salawu (1997) Eng. Struct. | Allemang (2003) Sound Vib. | Farrar & Jauregui (1998) J. Struct. Eng. | Feldman (2011) Wiley | Pandey et al. (1991, 1994) J. Sound Vib. | Brincker et al. (2001) Smart Mater. | Brownjohn (2007) Phil. Trans. Royal Soc.]
  ]
]
