import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 1. FILE PATHS
# ============================================================

credit_file = "../data/raw/tr_cre.csv"


# ============================================================
# 2. ANALYSIS SETTINGS
# ============================================================

BANK_LEI = "2G5BKIC2CB69PRJH1W31"
BANK_NAME = "Barclays Bank Ireland plc"

ANALYSIS_PERIOD = 202506


# ============================================================
# 3. LOAD DATA
# ============================================================

df = pd.read_csv(
    credit_file
)

bank_data = df[
    df["LEI_Code"] == BANK_LEI
].copy()


if bank_data.empty:
    raise ValueError(
        f"No observations found for {BANK_NAME}"
    )


# ============================================================
# 4. SELECT THE SAME SA REGULATORY SLICE
# ============================================================

period_data = bank_data[
    (bank_data["Period"] == ANALYSIS_PERIOD)
    & (bank_data["Country"] == 0)
    & (bank_data["Country_rank"] == 0)
    & (bank_data["NACE_codes"] == 0)
    & (bank_data["Portfolio"] == 1)
    & (
        bank_data["Label"]
        == "Exposure value - by exposure class (SA_and_IRB)"
    )
].copy()


period_data = period_data[
    period_data["Amount"] > 0
].copy()


# ============================================================
# 5. BASELINE METRICS
# ============================================================

total_exposure = (
    period_data["Amount"]
    .sum()
)


defaulted_exposure = (
    period_data.loc[
        period_data["Exposure"] == 601,
        "Amount"
    ]
    .sum()
)


baseline_default_share = (
    defaulted_exposure
    / total_exposure
    * 100
)


print("\nBaseline:")
print(
    f"Total selected exposure: "
    f"{total_exposure:.2f}"
)

print(
    f"Defaulted exposure: "
    f"{defaulted_exposure:.2f}"
)

print(
    f"Defaulted exposure share: "
    f"{baseline_default_share:.3f}%"
)

# ============================================================
# 6. DEFINE STRESS SCENARIOS
# ============================================================

# The multiplier represents an assumed increase in
# defaulted exposure relative to the June 2025 baseline.
#
# These are hypothetical sensitivity scenarios rather than
# EBA regulatory stress-test assumptions.
scenarios = {
    "Baseline": 1.00,
    "Mild stress": 1.25,
    "Moderate stress": 1.50,
    "Severe stress": 2.00
}

# ============================================================
# 7. RUN SENSITIVITY SCENARIOS
# ============================================================

results = []


for scenario_name, multiplier in scenarios.items():

    stressed_default = (
        defaulted_exposure
        * multiplier
    )

    # Assume the increase in defaulted exposure represents
    # migration from non-defaulted exposure into the defaulted
    # category rather than growth in total exposure.
    #
    # Therefore, the total selected exposure is held constant.
    stressed_share = (
        stressed_default
        / total_exposure
        * 100
    )


    results.append(
        {
            "Scenario": scenario_name,
            "Default_multiplier": multiplier,
            "Defaulted_exposure": stressed_default,
            "Defaulted_share": stressed_share
        }
    )


stress_summary = pd.DataFrame(
    results
)


print("\nStress-scenario results:")

print(
    stress_summary.to_string(
        index=False
    )
)

# ============================================================
# 8. CONTINUOUS SENSITIVITY ANALYSIS
# ============================================================

# The discrete scenarios above provide easily interpretable
# stress cases.
#
# We now vary the defaulted-exposure multiplier continuously
# between 1 and 3 to examine the sensitivity of the selected
# defaulted-exposure share to progressively stronger stress.
#
# 1.0 -> baseline
# 2.0 -> twice the baseline defaulted exposure
# 3.0 -> three times the baseline defaulted exposure
multipliers = np.linspace(
    1.0,
    3.0,
    100
)


sensitivity = pd.DataFrame(
    {
        "Multiplier": multipliers
    }
)


sensitivity["Defaulted_exposure"] = (
    defaulted_exposure
    * sensitivity["Multiplier"]
)


# Total selected exposure is held constant.
sensitivity["Defaulted_share"] = (
    sensitivity["Defaulted_exposure"]
    / total_exposure
    * 100
)


print("\nSensitivity analysis:")

print(
    sensitivity
    .iloc[::10]
    .to_string(index=False)
)

# ============================================================
# 9. PLOT STRESS-SENSITIVITY CURVE
# ============================================================

fig, ax = plt.subplots(
    figsize=(8.6, 4.8)
)


# ------------------------------------------------------------
# Continuous sensitivity curve
# ------------------------------------------------------------

ax.plot(
    sensitivity["Multiplier"],
    sensitivity["Defaulted_share"],
    linewidth=1.9,
    label="Sensitivity curve"
)


# ------------------------------------------------------------
# Add discrete stress scenarios
# ------------------------------------------------------------

ax.scatter(
    stress_summary["Default_multiplier"],
    stress_summary["Defaulted_share"],
    s=58,
    edgecolor="black",
    linewidth=0.6,
    zorder=5,
    label="Stress scenarios"
)


# ------------------------------------------------------------
# Add scenario labels
# ------------------------------------------------------------

for _, row in stress_summary.iterrows():

    ax.annotate(
        row["Scenario"],
        xy=(
            row["Default_multiplier"],
            row["Defaulted_share"]
        ),
        xytext=(7, 7),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=8.3
    )


# ------------------------------------------------------------
# Axis labels
# ------------------------------------------------------------

ax.set_xlabel(
    "Defaulted-exposure multiplier",
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
    "Defaulted-Exposure Sensitivity",
    fontsize=12.5,
    fontweight="semibold",
    pad=20
)

ax.text(
    0,
    1.01,
    f"{BANK_NAME} | Selected SA exposure-class slice | June 2025",
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
    axis="both",
    linestyle="--",
    linewidth=0.45,
    alpha=0.25
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

# Add controlled margins so annotations and endpoints
# do not touch the frame.
x_min = sensitivity["Multiplier"].min()
x_max = sensitivity["Multiplier"].max()

y_min = sensitivity["Defaulted_share"].min()
y_max = sensitivity["Defaulted_share"].max()

x_range = x_max - x_min
y_range = y_max - y_min

ax.set_xlim(
    x_min - 0.05 * x_range,
    x_max + 0.05 * x_range
)

ax.set_ylim(
    y_min - 0.08 * y_range,
    y_max + 0.08 * y_range
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
# Legend
# ------------------------------------------------------------

ax.legend(
    loc="upper left",
    frameon=False,
    fontsize=8.5,
    handlelength=2
)


# ------------------------------------------------------------
# Source and interpretation note
# ------------------------------------------------------------

ax.text(
    1.0,
    -0.14,
    "Source: EBA | Hypothetical sensitivity scenarios",
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
# Save figure
# ------------------------------------------------------------

plt.savefig(
    "../figures/barclays_defaulted_exposure_stress_sensitivity_202506.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    "../figures/barclays_defaulted_exposure_stress_sensitivity_202506.pdf",
    bbox_inches="tight"
)

plt.show()
# ============================================================
# 10. SENSITIVITY COEFFICIENT
# ============================================================

sensitivity_coefficient = (
    defaulted_exposure
    / total_exposure
    * 100
)

print("\nSensitivity coefficient:")

print(
    f"{sensitivity_coefficient:.6f} "
    "percentage points per unit multiplier"
)