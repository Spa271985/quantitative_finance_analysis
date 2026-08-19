# European Bank Credit-Risk Analysis

A reproducible quantitative study of publicly available European Banking
Authority (EBA) credit-risk data, using **Barclays Bank Ireland plc** as
the principal case study.

The project was developed as a learning and portfolio exercise in
quantitative risk analysis. It applies a scientific workflow---data
inspection, metric construction, validation, comparative analysis,
concentration measurement, and sensitivity testing---to regulatory
banking data.

## Project objectives

The analysis asks five practical questions:

1.  how is the selected Standardised Approach (SA) credit exposure
    distributed across exposure classes?
2.  how has defaulted exposure, both in absolute terms and as a share of
    exposure, evolved across reporting periods?
3.  how concentrated is the exposure-class distribution?
4.  how does Barclays Bank Ireland compare with selected Irish and Dutch
    reporting institutions?
5.  how sensitive is the observed defaulted-exposure share to
    hypothetical increases in defaulted exposure?

The project is intentionally transparent and relatively simple. It is
not intended to reproduce an internal bank credit-risk model or an
official EBA stress test.

## Data source

The project uses public data from the **European Banking Authority (EBA)
Transparency Exercise / Aggregate Statistical Data**.

The principal institution is:

-   **Bank:** Barclays Bank Ireland plc
-   **LEI:** `2G5BKIC2CB69PRJH1W31`
-   **latest period analysed:** June 2025 (`202506`)

The raw files used by the scripts are:

``` text
data/raw/
├── tr_cre.csv
└── TR_Metadata.xlsx
```

`tr_cre.csv` contains the credit-risk observations. `TR_Metadata.xlsx`
supplies metadata used to translate regulatory codes into readable
exposure-class and institution descriptions.

Raw EBA files are not committed to this repository. They should be
downloaded from the original EBA source and placed in `data/raw/`.

## Repository structure

``` text
european-bank-credit-risk-analysis/
│
├── README.md
├── requirements.txt
├── .gitignore
├── mathematical_methods.tex
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── 01_data_exploration.py
│   ├── 02_exposure_analysis.py
│   ├── 03_risk_trend.py
│   ├── 04_concentration_analysis.py
│   ├── 05_peer_comparison.py
│   └── 06_stress_analysis.py
│
└── figures/
    └── publication-quality PNG figures
```

## Analytical workflow

### 1. data exploration

`01_data_exploration.py` inspects the EBA credit-risk dataset, its
dimensions, missing values, reporting periods, regulatory measures, and
portfolio codes. It then extracts the observations belonging to Barclays
Bank Ireland.

The source dataset contains approximately 649,000 observations across
120 reporting institutions. Barclays Bank Ireland has observations for
September 2024, December 2024, March 2025, and June 2025.

### 2. exposure-class composition

`02_exposure_analysis.py` studies the selected Standardised Approach
exposure-class slice for June 2025.

For each exposure class (i), its portfolio share is

\[ s_i = `\frac{E_i}{\sum_j E_j}`{=tex}, \]

where (E_i) is the exposure value for class (i).

The analysis shows that the selected exposure distribution is dominated
by central governments / central banks, followed by corporates and
institutions.

### 3. defaulted-exposure trend

`03_risk_trend.py` follows total selected exposure and exposure
classified as defaulted across the four reporting periods.

\[ D_t =
`\frac{E_{\mathrm{default},t}}{E_{\mathrm{total},t}}`{=tex}`\times100`{=tex}.
\]

  period       total exposure   defaulted exposure   defaulted share
  ---------- ---------------- -------------------- -----------------
  Sep 2024          67,799.24               424.60            0.626%
  Dec 2024          68,330.28               334.18            0.489%
  Mar 2025          63,167.06               281.07            0.445%
  Jun 2025          63,176.87               367.87            0.582%

The series falls through March 2025 before increasing again in June
2025.

### 4. exposure concentration

`04_concentration_analysis.py` measures exposure-class concentration
using the **Herfindahl--Hirschman Index (HHI)**:

\[ HHI_t = `\sum`{=tex}*i s*{i,t}\^{,2}. \]

A larger HHI indicates that exposure is concentrated in fewer classes; a
smaller value indicates a more dispersed exposure distribution.

  period         HHI   top-3 share   largest-class share
  ---------- ------- ------------- ---------------------
  Sep 2024     0.337        88.86%                47.22%
  Dec 2024     0.336        88.45%                48.11%
  Mar 2025     0.396        93.99%                54.59%
  Jun 2025     0.381        93.24%                53.66%

### 5. peer comparison

`05_peer_comparison.py` places Barclays Bank Ireland in a
two-dimensional descriptive risk-profile space:

-   **x-axis:** exposure-class concentration (HHI)
-   **y-axis:** defaulted-exposure share (%)

Irish and Dutch reporting institutions are displayed together, while
Barclays Bank Ireland is highlighted separately. Irish peer medians are
included as reference lines.

This is a descriptive comparison rather than a ranking. Business model,
portfolio structure, geography, and reporting composition can materially
affect both metrics.

### 6. hypothetical stress sensitivity

`06_stress_analysis.py` studies how the June 2025 defaulted-exposure
share responds to hypothetical increases in defaulted exposure while
holding total selected exposure constant.

\[ E\_{`\mathrm{default}`{=tex}}(m)=mE\_{`\mathrm{default}`{=tex},0} \]

and

\[
D(m)=`\frac{mE_{\mathrm{default},0}}{E_{\mathrm{total},0}}`{=tex}`\times100`{=tex}.
\]

  scenario            multiplier   defaulted exposure   defaulted share
  ----------------- ------------ -------------------- -----------------
  baseline                  1.00               367.87            0.582%
  mild stress               1.25               459.84            0.728%
  moderate stress           1.50               551.81            0.873%
  severe stress             2.00               735.75            1.165%

A continuous multiplier scan from 1 to 3 is also used. Since total
exposure is held fixed, the response is linear by construction:

\[ `\frac{\partial D}{\partial m}`{=tex}=D_0. \]

For June 2025, this is approximately **0.582 percentage points per unit
multiplier**.

## Key observations

The selected SA exposure distribution is highly concentrated in a small
number of exposure classes. The defaulted-exposure share decreased from
September 2024 to March 2025 before partially reversing in June 2025.
Exposure-class concentration increased materially in March 2025 and
remained above its September/December 2024 level in June.

The peer analysis also illustrates that concentration and
defaulted-exposure share are distinct dimensions. A concentrated
exposure structure does not, by itself, imply a high observed
defaulted-exposure share.

The stress exercise is a **sensitivity analysis**, not a forecast of
future losses or defaults.

## Mathematical methods

A separate LaTeX companion, `mathematical_methods.tex`, documents the
mathematical concepts used in the project:

-   exposure normalization and shares;
-   defaulted-exposure ratios;
-   Herfindahl--Hirschman concentration;
-   top-(k) concentration;
-   peer medians;
-   stress multipliers;
-   continuous sensitivity and derivatives.

It can be compiled independently to produce a mathematical-methods PDF
for the repository.

## Installation

``` bash
pip install -r requirements.txt
```

The project uses pandas, NumPy, Matplotlib, seaborn, and openpyxl.

## Running the analysis

``` bash
python src/01_data_exploration.py
python src/02_exposure_analysis.py
python src/03_risk_trend.py
python src/04_concentration_analysis.py
python src/05_peer_comparison.py
python src/06_stress_analysis.py
```

Processed outputs are written to `data/processed/`, while figures are
saved under `figures/`.

## Reproducibility and design

The scripts use a common bank identifier and explicit filtering rules.
Intermediate calculations are printed so that key quantities can be
inspected and cross-checked before plotting. Figures use a consistent
publication-style design so that the repository can be read both as code
and as a compact quantitative study.

## Limitations

This project uses public aggregate regulatory data and therefore does
not contain borrower-level information, contractual cash flows, internal
ratings, probability of default (PD), loss given default (LGD), exposure
at default (EAD), collateral modelling, or bank-specific model
parameters.

Consequently:

-   the analysis is descriptive and exploratory;
-   the defaulted-exposure ratio is not a probability-of-default
    estimate;
-   HHI measures exposure-class concentration, not credit quality;
-   peer comparisons do not control for differences in business model or
    portfolio composition;
-   stress multipliers are hypothetical assumptions and are not
    calibrated macroeconomic scenarios;
-   the analysis is not an EBA regulatory stress test, capital model,
    expected-loss model, or investment recommendation.

## Disclaimer

This repository is an independent educational and portfolio project
based solely on publicly available EBA data. It is not affiliated with,
endorsed by, or produced for Barclays Bank Ireland plc, Barclays, the
European Banking Authority, or any other institution shown in the
analysis.

All interpretations are the author's own and are provided to demonstrate
quantitative analysis, programming, data interpretation, and
risk-analysis methodology. Nothing in this repository should be
interpreted as an assessment of the financial condition,
creditworthiness, regulatory compliance, or future performance of any
institution.
