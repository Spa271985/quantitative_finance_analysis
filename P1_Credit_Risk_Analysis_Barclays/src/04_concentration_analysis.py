import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. FILE PATHS
# ============================================================

credit_file = "../data/raw/tr_cre.csv"


# ============================================================
# 2. SELECT BANK
# ============================================================

BANK_LEI = "2G5BKIC2CB69PRJH1W31"
BANK_NAME = "Barclays Bank Ireland plc"


# ============================================================
# 3. LOAD DATA
# ============================================================

df = pd.read_csv(credit_file)

bank_data = df[
    df["LEI_Code"] == BANK_LEI
].copy()

if bank_data.empty:
    raise ValueError(
        f"No observations found for {BANK_NAME} "
        f"with LEI {BANK_LEI}"
    )

# ============================================================
# 4. IDENTIFY AVAILABLE REPORTING PERIODS
# ============================================================

periods = sorted(
    bank_data["Period"].unique()
)

print("\nReporting periods:")
print(periods)

# ============================================================
# 5. CALCULATE CONCENTRATION METRICS
# ============================================================

results = []

for period in periods:

    # Select the same regulatory slice used throughout
    # the previous analyses.
    period_data = bank_data[
        (bank_data["Period"] == period)
        & (bank_data["Country"] == 0)
        & (bank_data["Country_rank"] == 0)
        & (bank_data["NACE_codes"] == 0)
        & (bank_data["Portfolio"] == 1)
        & (
            bank_data["Label"]
            == "Exposure value - by exposure class (SA_and_IRB)"
        )
    ].copy()

    # Keep only positive exposure amounts.
    period_data = period_data[
        period_data["Amount"] > 0
    ].copy()

    total_exposure = period_data["Amount"].sum()

    if total_exposure == 0:
        continue

    # Calculate each exposure class's fraction of total exposure.
    period_data["Share"] = (
        period_data["Amount"]
        / total_exposure
    )

    # --------------------------------------------------------
    # HHI
    # --------------------------------------------------------

    # Square each exposure share and add the squared shares.
    hhi = (
        period_data["Share"] ** 2
    ).sum()

    # --------------------------------------------------------
    # Top-three concentration
    # --------------------------------------------------------

    top_three_exposure = (
        period_data
        .nlargest(3, "Amount")["Amount"]
        .sum()
    )

    top_three_share = (
        top_three_exposure
        / total_exposure
        * 100
    )

    # --------------------------------------------------------
    # Largest single exposure class
    # --------------------------------------------------------

    largest_row = (
        period_data
        .nlargest(1, "Amount")
        .iloc[0]
    )

    largest_exposure_share = (
        largest_row["Amount"]
        / total_exposure
        * 100
    )

    results.append(
        {
            "Period": period,
            "Total_exposure": total_exposure,
            "HHI": hhi,
            "Top3_share": top_three_share,
            "Largest_class_share": largest_exposure_share,
            "Largest_exposure_code": int(
                largest_row["Exposure"]
            ),
        }
    )

    # ============================================================
    # 6. CREATE CONCENTRATION SUMMARY
    # ============================================================

    # This section must remain OUTSIDE the for-loop.
    # The loop above first calculates metrics for all reporting periods.
    # Only afterwards do we convert all stored results into a table.
    concentration_summary = pd.DataFrame(
        results
    )

    print("\nConcentration-risk summary:")

    print(
        concentration_summary.to_string(
            index=False
        )
    )

    # ============================================================
    # 7. CREATE READABLE PERIOD LABELS
    # ============================================================

    period_labels = {
        202409: "Sep 2024",
        202412: "Dec 2024",
        202503: "Mar 2025",
        202506: "Jun 2025",
    }

    concentration_summary["Period_label"] = (
        concentration_summary["Period"]
        .map(period_labels)
    )

    # ============================================================
    # 8. PLOT EXPOSURE-CLASS CONCENTRATION
    # ============================================================

    fig, ax = plt.subplots(
        figsize=(8.6, 4.8)
    )

    # ------------------------------------------------------------
    # Plot HHI trend
    # ------------------------------------------------------------

    ax.plot(
        concentration_summary["Period_label"],
        concentration_summary["HHI"],
        marker="o",
        linewidth=1.9,
        markersize=5.5
    )

    # ------------------------------------------------------------
    # Add numerical labels above each point
    # ------------------------------------------------------------

    for x, y in zip(
            concentration_summary["Period_label"],
            concentration_summary["HHI"]
    ):
        ax.annotate(
            f"{y:.3f}",
            xy=(x, y),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5
        )

    # ------------------------------------------------------------
    # Axis labels
    # ------------------------------------------------------------

    ax.set_xlabel(
        "Reporting period",
        fontsize=10,
        labelpad=7
    )

    ax.set_ylabel(
        "Exposure-class HHI",
        fontsize=10,
        labelpad=8
    )

    # ------------------------------------------------------------
    # Title and subtitle
    # ------------------------------------------------------------

    ax.set_title(
        "SA Exposure-Class Concentration",
        fontsize=12.5,
        fontweight="semibold",
        pad=20
    )

    ax.text(
        0,
        1.01,
        f"{BANK_NAME} | Herfindahl–Hirschman Index of selected SA exposure distribution",
        transform=ax.transAxes,
        fontsize=8.5,
        alpha=0.70,
        ha="left",
        va="bottom"
    )

    # ------------------------------------------------------------
    # Grid
    # ------------------------------------------------------------

    ax.set_axisbelow(True)

    ax.grid(
        axis="y",
        linestyle="--",
        linewidth=0.45,
        alpha=0.25
    )

    ax.grid(
        axis="x",
        visible=False
    )

    # ------------------------------------------------------------
    # Full scientific frame
    # ------------------------------------------------------------

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.7)
        spine.set_color("black")

    # ------------------------------------------------------------
    # Axis limits
    # ------------------------------------------------------------

    # Add controlled headroom so the highest HHI annotation
    # does not collide with the subtitle or frame.
    y_min = concentration_summary["HHI"].min()
    y_max = concentration_summary["HHI"].max()

    y_range = y_max - y_min

    ax.set_ylim(
        y_min - 0.10 * y_range,
        y_max + 0.18 * y_range
    )

    # ------------------------------------------------------------
    # Tick formatting
    # ------------------------------------------------------------

    ax.tick_params(
        axis="both",
        labelsize=8.5,
        width=0.7,
        length=3,
        direction="out"
    )

    # ------------------------------------------------------------
    # Source information
    # ------------------------------------------------------------

    ax.text(
        1.0,
        -0.14,
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

    # ------------------------------------------------------------
    # Save publication-quality figures
    # ------------------------------------------------------------

    plt.savefig(
        "../figures/barclays_exposure_class_hhi_trend.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.savefig(
        "../figures/barclays_exposure_class_hhi_trend.pdf",
        bbox_inches="tight"
    )

    plt.show()