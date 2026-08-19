import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


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
# 4. DEFINE REPORTING PERIODS
# ============================================================

# Use all available reporting periods for the selected bank.
periods = sorted(
    bank_data["Period"].unique()
)

print("\nReporting periods:")
print(periods)


# ============================================================
# 5. CALCULATE RISK METRICS FOR EACH PERIOD
# ============================================================

results = []

for period in periods:

    # Select the same clean regulatory slice used in
    # the exposure-analysis script.
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

    # Keep only non-zero exposure values.
    period_data = period_data[
        period_data["Amount"] > 0
    ].copy()

    # Total selected SA exposure.
    total_exposure = period_data["Amount"].sum()

    # Exposure code 601 = Exposures in default.
    defaulted_exposure = (
        period_data.loc[
            period_data["Exposure"] == 601,
            "Amount"
        ]
        .sum()
    )

    # Share of selected exposure classified as defaulted.
    if total_exposure > 0:
        defaulted_share = (
            defaulted_exposure
            / total_exposure
            * 100
        )
    else:
        defaulted_share = 0.0

    # Store one row of results.
    results.append(
        {
            "Period": period,
            "Total_exposure": total_exposure,
            "Defaulted_exposure": defaulted_exposure,
            "Defaulted_share": defaulted_share
        }
    )


# ============================================================
# 6. CREATE SUMMARY TABLE
# ============================================================

risk_summary = pd.DataFrame(results)

print("\nCredit-risk trend summary:")
print(
    risk_summary.to_string(
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

risk_summary["Period_label"] = (
    risk_summary["Period"]
    .map(period_labels)
)

# ============================================================
# 8. PLOT DEFAULTED EXPOSURE SHARE OVER TIME
# ============================================================

sns.set_theme(
    style="white",
    context="paper"
)

fig, ax = plt.subplots(
    figsize=(8.6, 4.8)
)

ax.plot(
    risk_summary["Period_label"],
    risk_summary["Defaulted_share"],
    marker="o",
    linewidth=1.9,
    markersize=5.5
)


# ------------------------------------------------------------
# Add value labels
# ------------------------------------------------------------

for x, y in zip(
    risk_summary["Period_label"],
    risk_summary["Defaulted_share"]
):
    ax.annotate(
        f"{y:.3f}%",
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
    "Defaulted exposure share (%)",
    fontsize=10,
    labelpad=8
)


# ------------------------------------------------------------
# Title and subtitle
# ------------------------------------------------------------

ax.set_title(
    "Defaulted Exposure Share",
    fontsize=12.5,
    fontweight="semibold",
    pad=20
)

ax.text(
    0,
    1.01,
    f"{BANK_NAME} | Selected SA exposure-class slice",
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

# Add controlled headroom so the first annotation does not
# collide with the subtitle or frame.
y_min = risk_summary["Defaulted_share"].min()
y_max = risk_summary["Defaulted_share"].max()

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


plt.tight_layout(
    pad=1.0
)

plt.savefig(
    "../figures/barclays_defaulted_exposure_share_trend.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    "../figures/barclays_defaulted_exposure_share_trend.pdf",
    bbox_inches="tight"
)

plt.show()


# ============================================================
# 9. PLOT DEFAULTED EXPOSURE AMOUNT
# ============================================================

fig, ax = plt.subplots(
    figsize=(8.6, 4.8)
)

ax.plot(
    risk_summary["Period_label"],
    risk_summary["Defaulted_exposure"],
    marker="o",
    linewidth=1.9,
    markersize=5.5
)


# ------------------------------------------------------------
# Add value labels
# ------------------------------------------------------------

for x, y in zip(
    risk_summary["Period_label"],
    risk_summary["Defaulted_exposure"]
):
    ax.annotate(
        f"{y:,.0f}",
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
    "Defaulted exposure",
    fontsize=10,
    labelpad=8
)


# ------------------------------------------------------------
# Title and subtitle
# ------------------------------------------------------------

ax.set_title(
    "Defaulted Exposure",
    fontsize=12.5,
    fontweight="semibold",
    pad=20
)

ax.text(
    0,
    1.01,
    f"{BANK_NAME} | Selected SA exposure-class slice",
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

y_min = risk_summary["Defaulted_exposure"].min()
y_max = risk_summary["Defaulted_exposure"].max()

y_range = y_max - y_min

ax.set_ylim(
    y_min - 0.12 * y_range,
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


plt.tight_layout(
    pad=1.0
)

plt.savefig(
    "../figures/barclays_defaulted_exposure_trend.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    "../figures/barclays_defaulted_exposure_trend.pdf",
    bbox_inches="tight"
)

plt.show()