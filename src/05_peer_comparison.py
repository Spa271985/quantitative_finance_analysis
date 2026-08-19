import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# 1. FILE PATHS
# ============================================================

# Main EBA credit-risk dataset.
credit_file = "../data/raw/tr_cre.csv"

# EBA metadata workbook containing institution names,
# country information and dimension mappings.
metadata_file = "../data/raw/TR_Metadata.xlsx"


# ============================================================
# 2. ANALYSIS SETTINGS
# ============================================================

# Reference institution used throughout the project.
BANK_LEI = "2G5BKIC2CB69PRJH1W31"
BANK_NAME = "Barclays Bank Ireland plc"

# Latest reporting period used for the peer comparison.
ANALYSIS_PERIOD = 202506


# ============================================================
# 3. LOAD CREDIT-RISK DATA
# ============================================================

df = pd.read_csv(
    credit_file
)

print("\nCredit-risk observations:")
print(len(df))

print("\nUnique institutions:")
print(df["LEI_Code"].nunique())


# ============================================================
# 4. LOAD INSTITUTION METADATA
# ============================================================

# The first row of the Excel worksheet contains a title.
# The second row contains the actual column names.
#
# header=1 therefore tells pandas to use the second Excel row
# as the DataFrame header.
institution_metadata = pd.read_excel(
    metadata_file,
    sheet_name="List of Institutions",
    header=1
)

print("\nInstitution metadata columns:")
print(
    institution_metadata.columns.tolist()
)


# Keep only the metadata columns required for this analysis.
bank_names = institution_metadata[
    [
        "LEI_Code",
        "Name",
        "Desc_country"
    ]
].copy()


# ============================================================
# 5. CREATE UNIQUE LIST OF REPORTING INSTITUTIONS
# ============================================================

# Each bank appears many times in the credit-risk dataset.
# Reduce the data to one LEI / NSA pair per institution.
#
# NSA identifies the reporting jurisdiction associated
# with the institution.
institution_list = (
    df[
        [
            "LEI_Code",
            "NSA"
        ]
    ]
    .drop_duplicates()
    .copy()
)


print("\nInstitutions by reporting jurisdiction:")

print(
    institution_list["NSA"]
    .value_counts()
    .sort_index()
)


# ============================================================
# 6. IDENTIFY IRISH AND DUTCH REPORTING INSTITUTIONS
# ============================================================

# Barclays Bank Ireland is the reference institution.
#
# The Irish reporting group provides the closest geographic
# comparison available in this EBA dataset.
#
# Dutch institutions are included as an additional
# cross-country comparison group.
irish_institutions = institution_list[
    institution_list["NSA"] == "IE"
].copy()

dutch_institutions = institution_list[
    institution_list["NSA"] == "NL"
].copy()


# Combine the two peer groups.
peer_universe = pd.concat(
    [
        irish_institutions,
        dutch_institutions
    ],
    ignore_index=True
)


# ============================================================
# 7. ADD READABLE INSTITUTION NAMES
# ============================================================

# Merge LEI codes with institution names and countries
# from the metadata workbook.
peer_universe = peer_universe.merge(
    bank_names,
    on="LEI_Code",
    how="left"
)


print("\nPeer institutions:")

print(
    peer_universe[
        [
            "Name",
            "Desc_country",
            "LEI_Code",
            "NSA"
        ]
    ]
    .sort_values(
        [
            "NSA",
            "Name"
        ]
    )
    .to_string(
        index=False
    )
)


# ============================================================
# 8. DEFINE REUSABLE CREDIT-METRICS FUNCTION
# ============================================================

def calculate_credit_metrics(
    credit_data,
    bank_lei,
    period
):
    """
    Calculate selected Standardised Approach (SA) credit-risk
    metrics for one EBA institution.

    The same regulatory slice is applied to every institution
    so that the resulting metrics are comparable.

    Metrics returned:
        - Total selected SA exposure
        - Defaulted exposure
        - Defaulted exposure share
        - Exposure-class HHI
        - Top-three exposure-class share
        - Largest exposure-class share
        - Largest exposure-class code
    """

    # --------------------------------------------------------
    # Select one institution and reporting period
    # --------------------------------------------------------

    bank_period = credit_data[
        (credit_data["LEI_Code"] == bank_lei)
        & (credit_data["Period"] == period)
        & (credit_data["Country"] == 0)
        & (credit_data["Country_rank"] == 0)
        & (credit_data["NACE_codes"] == 0)
        & (credit_data["Portfolio"] == 1)
        & (
            credit_data["Label"]
            == "Exposure value - by exposure class (SA_and_IRB)"
        )
    ].copy()


    # Keep only positive exposure values.
    bank_period = bank_period[
        bank_period["Amount"] > 0
    ].copy()


    # If no comparable SA data are available,
    # return None rather than forcing a calculation.
    if bank_period.empty:
        return None


    # --------------------------------------------------------
    # Total selected SA exposure
    # --------------------------------------------------------

    total_exposure = (
        bank_period["Amount"]
        .sum()
    )

    if total_exposure <= 0:
        return None


    # --------------------------------------------------------
    # Defaulted exposure
    # --------------------------------------------------------

    # Exposure code 601 corresponds to:
    # "Exposures in default".
    defaulted_exposure = (
        bank_period.loc[
            bank_period["Exposure"] == 601,
            "Amount"
        ]
        .sum()
    )


    defaulted_share = (
        defaulted_exposure
        / total_exposure
        * 100
    )


    # --------------------------------------------------------
    # Exposure-class shares
    # --------------------------------------------------------

    bank_period["Share"] = (
        bank_period["Amount"]
        / total_exposure
    )


    # --------------------------------------------------------
    # Herfindahl-Hirschman Index (HHI)
    # --------------------------------------------------------

    # HHI is calculated as the sum of squared exposure-class
    # shares.
    #
    # A larger value indicates a more concentrated
    # exposure-class distribution.
    hhi = (
        bank_period["Share"] ** 2
    ).sum()


    # --------------------------------------------------------
    # Top-three exposure concentration
    # --------------------------------------------------------

    top_three_exposure = (
        bank_period
        .nlargest(
            3,
            "Amount"
        )["Amount"]
        .sum()
    )


    top_three_share = (
        top_three_exposure
        / total_exposure
        * 100
    )


    # --------------------------------------------------------
    # Largest exposure class
    # --------------------------------------------------------

    largest_row = (
        bank_period
        .nlargest(
            1,
            "Amount"
        )
        .iloc[0]
    )


    largest_class_share = (
        largest_row["Amount"]
        / total_exposure
        * 100
    )


    # --------------------------------------------------------
    # Return all metrics for this institution
    # --------------------------------------------------------

    return {
        "LEI_Code": bank_lei,
        "Total_exposure": total_exposure,
        "Defaulted_exposure": defaulted_exposure,
        "Defaulted_share": defaulted_share,
        "HHI": hhi,
        "Top3_share": top_three_share,
        "Largest_class_share": largest_class_share,
        "Largest_exposure_code": int(
            largest_row["Exposure"]
        ),
    }


# ============================================================
# 9. CALCULATE METRICS FOR EVERY PEER
# ============================================================

peer_results = []


for _, row in peer_universe.iterrows():

    bank_lei = row["LEI_Code"]
    bank_name = row["Name"]
    bank_country = row["Desc_country"]
    bank_nsa = row["NSA"]


    metrics = calculate_credit_metrics(
        df,
        bank_lei,
        ANALYSIS_PERIOD
    )


    # Some institutions may not have a comparable
    # Standardised Approach exposure slice.
    if metrics is None:

        print(
            f"Skipping {bank_name}: "
            "no comparable SA exposure data."
        )

        continue


    # Add institution information to the calculated metrics.
    metrics["Bank_name"] = bank_name
    metrics["Country"] = bank_country
    metrics["NSA"] = bank_nsa


    peer_results.append(
        metrics
    )


# ============================================================
# 10. CREATE PEER COMPARISON TABLE
# ============================================================

peer_summary = pd.DataFrame(
    peer_results
)


# Arrange columns in a clear order.
peer_summary = peer_summary[
    [
        "Bank_name",
        "Country",
        "NSA",
        "LEI_Code",
        "Total_exposure",
        "Defaulted_exposure",
        "Defaulted_share",
        "HHI",
        "Top3_share",
        "Largest_class_share",
        "Largest_exposure_code",
    ]
]


print("\nPeer comparison metrics:")

print(
    peer_summary
    .sort_values(
        [
            "Country",
            "Defaulted_share"
        ]
    )
    .to_string(
        index=False
    )
)


# ============================================================
# 11. CALCULATE PEER-GROUP MEDIANS
# ============================================================

# Median is used instead of mean because the peer groups
# are relatively small and individual institutions may have
# substantially different portfolio structures.
#
# The median provides a more robust central benchmark.
peer_medians = (
    peer_summary
    .groupby(
        "Country"
    )
    [
        [
            "Defaulted_share",
            "HHI",
            "Top3_share",
            "Largest_class_share"
        ]
    ]
    .median()
)


print("\nPeer-group medians:")

print(
    peer_medians
    .to_string()
)


# ============================================================
# 12. IDENTIFY THE REFERENCE INSTITUTION
# ============================================================

barclays_rows = peer_summary[
    peer_summary["LEI_Code"] == BANK_LEI
]


if barclays_rows.empty:
    raise ValueError(
        f"{BANK_NAME} was not found in the peer comparison."
    )


barclays_result = (
    barclays_rows
    .iloc[0]
)


# ============================================================
# 13. CALCULATE IRISH PEER MEDIAN
# ============================================================

irish_peer_data = peer_summary[
    peer_summary["Country"] == "Ireland"
]


irish_median = (
    irish_peer_data[
        [
            "Defaulted_share",
            "HHI",
            "Top3_share",
            "Largest_class_share"
        ]
    ]
    .median()
)


# ============================================================
# 14. REPORT BARCLAYS METRICS
# ============================================================

print("\nReference institution:")
print(BANK_NAME)


print("\nBarclays Bank Ireland metrics:")

print(
    f"Defaulted exposure share: "
    f"{barclays_result['Defaulted_share']:.3f}%"
)

print(
    f"Exposure-class HHI: "
    f"{barclays_result['HHI']:.3f}"
)

print(
    f"Top-three exposure share: "
    f"{barclays_result['Top3_share']:.2f}%"
)

print(
    f"Largest exposure-class share: "
    f"{barclays_result['Largest_class_share']:.2f}%"
)


# ============================================================
# 15. REPORT IRISH PEER MEDIAN
# ============================================================

print("\nIrish reporting-group median:")

print(
    f"Defaulted exposure share: "
    f"{irish_median['Defaulted_share']:.3f}%"
)

print(
    f"Exposure-class HHI: "
    f"{irish_median['HHI']:.3f}"
)

print(
    f"Top-three exposure share: "
    f"{irish_median['Top3_share']:.2f}%"
)

print(
    f"Largest exposure-class share: "
    f"{irish_median['Largest_class_share']:.2f}%"
)


# ============================================================
# 16. CALCULATE BARCLAYS DIFFERENCE FROM IRISH MEDIAN
# ============================================================

# Positive values mean Barclays is above the Irish
# reporting-group median for that metric.
#
# Negative values mean Barclays is below the median.
defaulted_difference = (
    barclays_result["Defaulted_share"]
    - irish_median["Defaulted_share"]
)

hhi_difference = (
    barclays_result["HHI"]
    - irish_median["HHI"]
)

top3_difference = (
    barclays_result["Top3_share"]
    - irish_median["Top3_share"]
)


print("\nBarclays relative to Irish reporting-group median:")

print(
    f"Defaulted exposure-share difference: "
    f"{defaulted_difference:+.3f} percentage points"
)

print(
    f"HHI difference: "
    f"{hhi_difference:+.3f}"
)

print(
    f"Top-three exposure-share difference: "
    f"{top3_difference:+.2f} percentage points"
)


# ============================================================
# 17. SAVE PEER COMPARISON RESULTS
# ============================================================

# Save the peer-level calculated metrics for later plotting,
# documentation and reproducibility.
output_file = (
    "../data/processed/"
    "irish_dutch_peer_comparison_202506.csv"
)


peer_summary.to_csv(
    output_file,
    index=False
)


print("\nPeer comparison results saved to:")
print(output_file)


print("\nPeer comparison completed successfully.")

# ============================================================
# 18. PLOT PEER COMPARISON:
#     DEFAULTED EXPOSURE SHARE VS EXPOSURE-CLASS HHI
# ============================================================

sns.set_theme(
    style="white",
    context="paper"
)


# A wider aspect ratio provides more horizontal room for
# institution labels and reduces label crowding.
fig, ax = plt.subplots(
    figsize=(11.5, 6.5)
)


# ------------------------------------------------------------
# Prepare peer groups
# ------------------------------------------------------------

irish_plot = peer_summary[
    peer_summary["Country"] == "Ireland"
]

dutch_plot = peer_summary[
    peer_summary["Country"] == "Netherlands"
]

barclays_plot = peer_summary[
    peer_summary["LEI_Code"] == BANK_LEI
]


# ------------------------------------------------------------
# Plot Irish institutions
# ------------------------------------------------------------

ax.scatter(
    irish_plot["HHI"],
    irish_plot["Defaulted_share"],
    s=85,
    alpha=0.80,
    label="Ireland",
    zorder=3
)


# ------------------------------------------------------------
# Plot Dutch institutions
# ------------------------------------------------------------

ax.scatter(
    dutch_plot["HHI"],
    dutch_plot["Defaulted_share"],
    s=85,
    alpha=0.80,
    marker="s",
    label="Netherlands",
    zorder=3
)


# ------------------------------------------------------------
# Highlight Barclays Bank Ireland
# ------------------------------------------------------------

ax.scatter(
    barclays_plot["HHI"],
    barclays_plot["Defaulted_share"],
    s=210,
    marker="*",
    edgecolor="black",
    linewidth=0.8,
    label=BANK_NAME,
    zorder=6
)


# ------------------------------------------------------------
# Add institution labels
# ------------------------------------------------------------

# Institution labels are deliberately offset from their
# markers to reduce visual overlap.
#
# Long institution names are shortened for readability.
for _, row in peer_summary.iterrows():

    label = row["Bank_name"]

    if len(label) > 27:
        label = label[:24] + "..."


    # Default position:
    # slightly above and to the right of the marker.
    x_offset = 6
    y_offset = 6
    horizontal_alignment = "left"


    # Institutions on the far-right side of the chart
    # are labelled to the left so the text remains
    # inside the plotting region.
    if row["HHI"] > 0.57:

        x_offset = -6
        horizontal_alignment = "right"


    # Very low defaulted-share observations are moved
    # upward slightly to prevent labels from crowding
    # the x-axis.
    if row["Defaulted_share"] < 0.05:

        y_offset = 9


    # Barclays receives a slightly stronger label.
    if row["LEI_Code"] == BANK_LEI:

        ax.annotate(
            label,
            xy=(
                row["HHI"],
                row["Defaulted_share"]
            ),
            xytext=(8, 7),
            textcoords="offset points",
            fontsize=12,
            fontweight="semibold",
            ha="left",
            va="bottom",
            zorder=7
        )

    else:

        ax.annotate(
            label,
            xy=(
                row["HHI"],
                row["Defaulted_share"]
            ),
            xytext=(
                x_offset,
                y_offset
            ),
            textcoords="offset points",
            fontsize=12.5,
            alpha=0.78,
            ha=horizontal_alignment,
            va="bottom",
            zorder=4
        )


# ------------------------------------------------------------
# Irish peer-group median reference lines
# ------------------------------------------------------------

irish_hhi_median = (
    irish_plot["HHI"].median()
)

irish_default_median = (
    irish_plot["Defaulted_share"].median()
)


ax.axvline(
    irish_hhi_median,
    linestyle="--",
    linewidth=0.9,
    alpha=0.45,
    zorder=1
)

ax.axhline(
    irish_default_median,
    linestyle="--",
    linewidth=0.9,
    alpha=0.45,
    zorder=1
)


# ------------------------------------------------------------
# Axis labels
# ------------------------------------------------------------

ax.set_xlabel(
    "Exposure-class concentration (HHI)",
    fontsize=15,
    labelpad=9
)

ax.set_ylabel(
    "Defaulted exposure share (%)",
    fontsize=15,
    labelpad=9
)


# ------------------------------------------------------------
# Title and subtitle
# ------------------------------------------------------------

ax.set_title(
    "Credit-Risk Profile: Irish and Dutch Institutions",
    fontsize=15,
    fontweight="semibold",
    pad=23
)

ax.text(
    0,
    1.012,
    "Selected Standardised Approach exposure-class data | June 2025",
    transform=ax.transAxes,
    fontsize=10,
    alpha=0.70,
    ha="left",
    va="bottom"
)


# ------------------------------------------------------------
# Grid
# ------------------------------------------------------------

ax.set_axisbelow(True)

ax.grid(
    axis="both",
    linestyle="--",
    linewidth=0.45,
    alpha=0.22
)


# ------------------------------------------------------------
# Complete scientific frame
# ------------------------------------------------------------

for spine in ax.spines.values():

    spine.set_visible(True)
    spine.set_linewidth(0.75)
    spine.set_color("black")


# ------------------------------------------------------------
# Tick formatting
# ------------------------------------------------------------

ax.tick_params(
    axis="both",
    labelsize=10.5,
    width=0.75,
    length=4,
    direction="out"
)


# ------------------------------------------------------------
# Add controlled plotting margins
# ------------------------------------------------------------

x_min = peer_summary["HHI"].min()
x_max = peer_summary["HHI"].max()

y_min = peer_summary["Defaulted_share"].min()
y_max = peer_summary["Defaulted_share"].max()

x_range = x_max - x_min
y_range = y_max - y_min


ax.set_xlim(
    x_min - 0.05 * x_range,
    x_max + 0.07 * x_range
)

ax.set_ylim(
    max(0, y_min - 0.06 * y_range),
    y_max + 0.08 * y_range
)


# ------------------------------------------------------------
# Legend
# ------------------------------------------------------------

ax.legend(
    loc="upper right",
    frameon=False,
    fontsize=15,
    markerscale=0.9,
    handletextpad=0.6,
    labelspacing=0.5
)


# ------------------------------------------------------------
# Source information
# ------------------------------------------------------------

ax.text(
    1.0,
    -0.135,
    "Source: European Banking Authority (EBA)",
    transform=ax.transAxes,
    ha="right",
    va="top",
    fontsize=8.5,
    alpha=0.65
)


# ------------------------------------------------------------
# Final layout
# ------------------------------------------------------------

plt.tight_layout(
    pad=1.1
)


# ------------------------------------------------------------
# Save figure
# ------------------------------------------------------------

plt.savefig(
    "../figures/irish_dutch_peer_hhi_defaulted_share_202506.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    "../figures/irish_dutch_peer_hhi_defaulted_share_202506.pdf",
    bbox_inches="tight"
)

plt.show()