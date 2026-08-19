import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# 1. FILE PATHS AND BASIC DATA LOADING
# ============================================================

# Main EBA credit-risk dataset.
credit_file = "../data/raw/tr_cre.csv"

# Metadata file containing descriptions for coded variables
# such as exposure classes.
metadata_file = "../data/raw/TR_Metadata.xlsx"

# Read the full EBA credit-risk CSV into a pandas DataFrame.
df = pd.read_csv(credit_file)


# ============================================================
# 2. SELECT THE BANK TO ANALYSE
# ============================================================

# Store the bank identifier and readable name in variables.
#
# This makes the script reusable. To analyse another EBA bank,
# only BANK_LEI and BANK_NAME need to be changed.
BANK_LEI = "2G5BKIC2CB69PRJH1W31"
BANK_NAME = "Barclays Bank Ireland plc"

# Reporting period to analyse.
#
# EBA periods use YYYYMM format:
# 202506 -> June 2025
ANALYSIS_PERIOD = 202506

# Human-readable version used in figure titles.
ANALYSIS_PERIOD_LABEL = "June 2025"


# Filter the complete EBA dataset using the bank's LEI.
bank_data = df[
    df["LEI_Code"] == BANK_LEI
].copy()


print("\nSelected bank:")
print(BANK_NAME)

print("\nNumber of observations for selected bank:")
print(bank_data.shape)


# Stop execution if the LEI does not exist in the dataset.
if bank_data.empty:
    raise ValueError(
        f"No observations found for {BANK_NAME} "
        f"with LEI {BANK_LEI}"
    )


# ============================================================
# 3. CREATE A SAFE BANK NAME FOR OUTPUT FILES
# ============================================================

# Convert the readable bank name into a filename-friendly form.
#
# Example:
# "Barclays Bank Ireland plc"
#
# becomes:
#
# "barclays_bank_ireland_plc"
safe_bank_name = (
    BANK_NAME
    .lower()
    .replace(" ", "_")
    .replace(".", "")
    .replace("/", "_")
)


# ============================================================
# 4. LOAD EXPOSURE-CLASS METADATA
# ============================================================

# The main CSV stores exposure classes as numerical codes
# such as 103, 203, 303, etc.
#
# The "Exposure" sheet in TR_Metadata.xlsx translates these
# numerical codes into readable names such as:
#
# 103 -> Central governments or central banks
# 203 -> Institutions
# 303 -> Corporates
exposure_metadata = pd.read_excel(
    metadata_file,
    sheet_name="Exposure"
)

print("\nExposure metadata:")
print(exposure_metadata.head(20))


# ============================================================
# 5. SELECT A CLEAN CREDIT-EXPOSURE SLICE
# ============================================================

# We want one clearly defined regulatory view of the portfolio
# before performing any aggregation.
#
# Period == ANALYSIS_PERIOD:
#     Select the chosen reporting date.
#
# Country == 0:
#     Total / no geographical breakdown.
#
# Country_rank == 0:
#     No country-ranking breakdown.
#
# NACE_codes == 0:
#     No economic-sector breakdown.
#
# Label:
#     Select "Exposure value by exposure class".
#
# These filters are important because regulatory data can contain
# several different views of the same underlying exposures.
#
# Summing across all dimensions could otherwise double-count
# the same economic exposure.
latest = bank_data[
    (bank_data["Period"] == ANALYSIS_PERIOD)
    & (bank_data["Country"] == 0)
    & (bank_data["Country_rank"] == 0)
    & (bank_data["NACE_codes"] == 0)
    & (
        bank_data["Label"]
        == "Exposure value - by exposure class (SA_and_IRB)"
    )
].copy()


print(
    f"\nShape of selected {ANALYSIS_PERIOD_LABEL} dataset:"
)
print(latest.shape)


# Inspect the main coded variables before adding readable labels.
print("\nSelected rows before metadata merge:")
print(
    latest[
        ["Portfolio", "Exposure", "Status", "Amount"]
    ]
)


# ============================================================
# 6. MERGE EXPOSURE CODES WITH HUMAN-READABLE DESCRIPTIONS
# ============================================================

# Merge the selected credit-risk data with the metadata table.
#
# Both tables contain a column called "Label".
#
# suffixes=("", "_description") keeps the original credit-risk
# Label unchanged while renaming the metadata label
# to "Label_description".
latest = latest.merge(
    exposure_metadata,
    on="Exposure",
    how="left",
    suffixes=("", "_description")
)


print("\nColumns after metadata merge:")
print(latest.columns)


# ============================================================
# 7. IMPROVE CONSOLE DISPLAY
# ============================================================

# By default, pandas may truncate long tables.
# These settings make the full output easier to inspect.
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)


print("\nFull selected exposure table:")
print(
    latest[
        [
            "Portfolio",
            "Exposure",
            "Label_description",
            "Status",
            "Amount",
        ]
    ].to_string(index=False)
)


# ============================================================
# 8. SEPARATE STANDARDISED APPROACH AND IRB
# ============================================================

# According to the EBA metadata:
#
# Portfolio == 1 -> Standardised Approach (SA)
# Portfolio == 2 -> Internal Ratings-Based Approach (IRB)
#
# These are kept separate because they represent different
# regulatory approaches for measuring credit risk.
sa = latest[
    latest["Portfolio"] == 1
].copy()

irb = latest[
    latest["Portfolio"] == 2
].copy()


print("\nSA exposure:")
print(
    sa[
        [
            "Exposure",
            "Label_description",
            "Status",
            "Amount",
        ]
    ].to_string(index=False)
)


print("\nIRB exposure:")
print(
    irb[
        [
            "Exposure",
            "Label_description",
            "Status",
            "Amount",
        ]
    ].to_string(index=False)
)


# Check how many SA rows belong to each default-status category.
#
# In this dataset:
#
# Status == 0 -> no default-status breakdown
# Status == 2 -> defaulted exposure
print("\nSA status counts:")
print(
    sa["Status"].value_counts()
)


# ============================================================
# 9. KEEP NON-ZERO SA EXPOSURES
# ============================================================

# Keep all SA exposure classes where the reported amount
# is greater than zero.
#
# Exposure code 601 ("Exposures in default") is intentionally
# retained because it is a legitimate regulatory exposure class.
sa_exposure = sa[
    sa["Amount"] > 0
].copy()


print("\nNon-zero SA exposure classes:")
print(
    sa_exposure[
        [
            "Exposure",
            "Label_description",
            "Status",
            "Amount",
        ]
    ].to_string(index=False)
)


# ============================================================
# 10. CALCULATE TOTAL SA EXPOSURE
# ============================================================

# Sum all non-zero SA exposure-class amounts in this selected
# regulatory slice.
#
# Important:
#
# This is described as:
#
# "Total exposure value in the selected SA exposure-class slice"
#
# rather than simply "total bank credit exposure", because
# the analysis represents one particular regulatory view.
total_sa_exposure = (
    sa_exposure["Amount"].sum()
)


print("\nTotal selected SA exposure:")
print(
    round(
        total_sa_exposure,
        2
    )
)


# ============================================================
# 11. CALCULATE EACH EXPOSURE CLASS'S SHARE
# ============================================================

# Convert each exposure amount into a percentage of the
# selected SA exposure total.
sa_exposure["Exposure_share"] = (
    sa_exposure["Amount"]
    / total_sa_exposure
    * 100
)


print("\nSA exposure composition:")
print(
    sa_exposure[
        [
            "Label_description",
            "Status",
            "Amount",
            "Exposure_share",
        ]
    ]
    .sort_values(
        "Amount",
        ascending=False
    )
    .to_string(index=False)
)


# ============================================================
# 12. CALCULATE DEFAULTED EXPOSURE
# ============================================================

# Exposure code 601 corresponds to:
#
# "Exposures in default"
#
# Extract the reported amount directly from the data.
defaulted_exposure = (
    sa_exposure.loc[
        sa_exposure["Exposure"] == 601,
        "Amount",
    ]
    .sum()
)


# Calculate defaulted exposure as a percentage of the selected
# SA exposure-class total.
#
# Important:
#
# This is NOT probability of default (PD).
#
# It is simply:
#
# defaulted exposure / selected exposure total
defaulted_exposure_share = (
    defaulted_exposure
    / total_sa_exposure
    * 100
)


print("\nDefaulted exposure:")
print(
    round(
        defaulted_exposure,
        2
    )
)


print("\nDefaulted exposure share:")
print(
    round(
        defaulted_exposure_share,
        3
    ),
    "%"
)


# ============================================================
# 13. CALCULATE EXPOSURE CONCENTRATION
# ============================================================

# Identify the three largest exposure classes.
top_three_exposure = (
    sa_exposure
    .nlargest(
        3,
        "Amount"
    )["Amount"]
    .sum()
)


# Calculate what percentage of the selected SA exposure
# is represented by the three largest exposure classes.
top_three_share = (
    top_three_exposure
    / total_sa_exposure
    * 100
)


print("\nTop-three exposure concentration:")
print(
    round(
        top_three_share,
        2
    ),
    "%"
)


# ============================================================
# 14. PRODUCE PUBLICATION-STYLE CREDIT-EXPOSURE CHART
# ============================================================

# Establish a clean scientific visual style.
sns.set_theme(
    style="white",
    context="paper"
)


# Sort exposure classes so that the largest category appears
# at the top of the horizontal bar chart.
plot_data = (
    sa_exposure
    .sort_values(
        "Amount",
        ascending=True
    )
    .copy()
)


# ------------------------------------------------------------
# Shorten long regulatory labels for readability
# ------------------------------------------------------------

label_map = {
    "Central governments or central banks":
        "Central governments / central banks",

    "Regional governments or local authorities":
        "Regional / local governments",

    "Multilateral Development Banks":
        "Multilateral development banks",

    "International Organisations":
        "International organisations",

    "Secured by mortgages on immovable property and ADC exposure":
        "Mortgage-secured / ADC",

    "Equity exposures":
        "Equity",

    "Exposures in default":
        "Defaulted exposures",

    "Other items":
        "Other",
}


plot_data["Plot_label"] = (
    plot_data["Label_description"]
    .replace(label_map)
)


# ------------------------------------------------------------
# Create figure
# ------------------------------------------------------------

# A slightly wider and shorter aspect ratio works better
# for a horizontal bar chart with this number of categories.
fig, ax = plt.subplots(
    figsize=(10.5, 5.8)
)


# ------------------------------------------------------------
# Draw horizontal bars
# ------------------------------------------------------------

bars = ax.barh(
    plot_data["Plot_label"],
    plot_data["Amount"],
    edgecolor="black",
    linewidth=0.45
)


# ------------------------------------------------------------
# Add numerical values at the end of each bar
# ------------------------------------------------------------

maximum = plot_data["Amount"].max()


for bar in bars:

    width = bar.get_width()

    ax.text(
        width + maximum * 0.012,
        bar.get_y() + bar.get_height() / 2,
        f"{width:,.0f}",
        va="center",
        ha="left",
        fontsize=8.5
    )


# ------------------------------------------------------------
# Axis labels
# ------------------------------------------------------------

ax.set_xlabel(
    "Exposure value",
    fontsize=10.5,
    labelpad=7
)

ax.set_ylabel("")


# ------------------------------------------------------------
# Main title
# ------------------------------------------------------------

ax.set_title(
    f"{BANK_NAME}: Standardised Approach Credit Exposure",
    fontsize=12,
    fontweight="semibold",
    pad=19
)


# ------------------------------------------------------------
# Subtitle
# ------------------------------------------------------------

ax.text(
    0,
    1.006,
    f"EBA Transparency Exercise | {ANALYSIS_PERIOD_LABEL}",
    transform=ax.transAxes,
    fontsize=8.5,
    alpha=0.70,
    ha="left",
    va="bottom"
)


# ------------------------------------------------------------
# Grid
# ------------------------------------------------------------

# Only vertical grid lines are useful for this horizontal
# quantitative comparison.
ax.set_axisbelow(True)

ax.grid(
    axis="x",
    linestyle="--",
    linewidth=0.45,
    alpha=0.25
)

ax.grid(
    axis="y",
    visible=False
)


# ------------------------------------------------------------
# Complete rectangular scientific frame
# ------------------------------------------------------------

for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(0.7)
    spine.set_color("black")


# ------------------------------------------------------------
# Axis range
# ------------------------------------------------------------

# Leave enough space for the numerical labels at the ends
# of the bars without producing excessive empty space.
ax.set_xlim(
    0,
    maximum * 1.14
)


# ------------------------------------------------------------
# Numerical formatting
# ------------------------------------------------------------

ax.xaxis.set_major_formatter(
    plt.FuncFormatter(
        lambda x, _: f"{x:,.0f}"
    )
)


# ------------------------------------------------------------
# Tick formatting
# ------------------------------------------------------------

ax.tick_params(
    axis="x",
    labelsize=8.5,
    width=0.7,
    length=3,
    direction="out"
)

ax.tick_params(
    axis="y",
    labelsize=9,
    width=0.7,
    length=0,
    pad=7
)


# ------------------------------------------------------------
# Source information
# ------------------------------------------------------------

# Position the source relative to the axes rather than the
# complete figure so that it aligns naturally with the plot.
ax.text(
    1.0,
    -0.115,
    "Source: European Banking Authority (EBA)",
    transform=ax.transAxes,
    ha="right",
    va="top",
    fontsize=7.5,
    alpha=0.65
)


# ------------------------------------------------------------
# Final layout
# ------------------------------------------------------------

plt.tight_layout(
    pad=1.0
)

# ============================================================
# 15. SAVE PUBLICATION-QUALITY FIGURES
# ============================================================

# Filenames are generated automatically from BANK_NAME.
#
# Therefore, if another bank is selected later,
# the saved output files also change automatically.
png_file = (
    f"../figures/"
    f"{safe_bank_name}_sa_exposure_by_class_"
    f"{ANALYSIS_PERIOD}.png"
)

pdf_file = (
    f"../figures/"
    f"{safe_bank_name}_sa_exposure_by_class_"
    f"{ANALYSIS_PERIOD}.pdf"
)


# Save high-resolution PNG for GitHub / README.
plt.savefig(
    png_file,
    dpi=300,
    bbox_inches="tight"
)


# Save vector PDF for reports or presentations.
plt.savefig(
    pdf_file,
    bbox_inches="tight"
)


print("\nFigures saved as:")
print(png_file)
print(pdf_file)


plt.show()