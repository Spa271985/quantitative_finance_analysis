import os
import pandas as pd


# ============================================================
# 1. FILE PATHS AND BASIC DATA LOADING
# ============================================================

# Main EBA credit-risk dataset downloaded from the
# European Banking Authority (EBA) Transparency Exercise.
credit_file = "../data/raw/tr_cre.csv"

# Read the complete EBA credit-risk CSV into a pandas DataFrame.
df = pd.read_csv(credit_file)


# ============================================================
# 2. INITIAL DATASET INSPECTION
# ============================================================

# Display the first five rows to understand the basic structure
# of the dataset.
print("\nFirst five rows:")
print(df.head())


# Show the number of observations (rows) and variables (columns).
print("\nDataset dimensions:")
print(df.shape)


# List all available variables.
print("\nColumn names:")
print(df.columns.tolist())


# Show:
# - column names
# - data types
# - non-null counts
# - approximate memory usage
print("\nDataset information:")
df.info()


# ============================================================
# 3. CHECK DATA QUALITY
# ============================================================

# Count missing observations in each column.
#
# This is an important first step before performing calculations,
# because missing values may affect later aggregation and modelling.
print("\nMissing values:")
print(
    df.isnull().sum()
)


# ============================================================
# 4. SELECT THE BANK TO ANALYSE
# ============================================================

# LEI = Legal Entity Identifier.
#
# The LEI uniquely identifies a financial institution.
#
# These two variables make the script reusable.
# To analyse another EBA institution later, change only:
#
# BANK_LEI
# BANK_NAME
BANK_LEI = "2G5BKIC2CB69PRJH1W31"
BANK_NAME = "Barclays Bank Ireland plc"


# Filter the full EBA dataset to retain only rows belonging
# to the selected bank.
bank_data = df[
    df["LEI_Code"] == BANK_LEI
].copy()


print("\nSelected bank:")
print(BANK_NAME)

print("\nNumber of observations for selected bank:")
print(bank_data.shape)


# Stop execution if the LEI is not present in the dataset.
if bank_data.empty:
    raise ValueError(
        f"No observations found for {BANK_NAME} "
        f"with LEI {BANK_LEI}"
    )


# ============================================================
# 5. INSPECT REPORTING PERIODS
# ============================================================

# Periods are stored in YYYYMM format.
#
# Example:
# 202409 -> September 2024
# 202412 -> December 2024
# 202503 -> March 2025
# 202506 -> June 2025
print("\nReporting periods:")

periods = sorted(
    bank_data["Period"].unique()
)

print(periods)


# ============================================================
# 6. INSPECT THE CREDIT-RISK MEASURES REPORTED
# ============================================================

# The "Label" column describes the regulatory quantity being reported.
#
# value_counts() shows how frequently each type of credit-risk measure
# occurs for the selected bank.
#
# Showing the 20 most common labels gives a quick overview of the
# information available before we decide what to analyse.
print("\nMost common credit-risk measures:")

print(
    bank_data["Label"]
    .value_counts()
    .head(20)
)


# ============================================================
# 7. INSPECT REGULATORY PORTFOLIO CODES
# ============================================================

# The "Portfolio" column identifies the regulatory approach.
#
# Important codes for this project include:
#
# Portfolio == 1 -> Standardised Approach (SA)
# Portfolio == 2 -> Internal Ratings-Based Approach (IRB)
#
# At this stage we only count the number of database rows.
#
# Important:
# Row counts are NOT the same as monetary exposure shares.
print("\nPortfolio codes:")

print(
    bank_data["Portfolio"]
    .value_counts()
    .sort_index()
)


# ============================================================
# 8. CREATE A SAFE BANK NAME FOR OUTPUT FILES
# ============================================================

# Convert the readable bank name into a filename-friendly form.
#
# Example:
#
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
# 9. SAVE THE SELECTED BANK SUBSET
# ============================================================

# Create the processed-data directory if it does not already exist.
os.makedirs(
    "../data/processed",
    exist_ok=True
)


# Store the selected bank dataset separately.
#
# This allows later scripts to work with a smaller processed file
# instead of repeatedly filtering the full ~649,000-row EBA dataset.
output_path = (
    f"../data/processed/"
    f"{safe_bank_name}_credit_risk.csv"
)


bank_data.to_csv(
    output_path,
    index=False
)


print("\nProcessed bank subset saved to:")
print(output_path)


# ============================================================
# 10. FINAL SUMMARY
# ============================================================

print("\nData exploration completed successfully.")

print(
    f"Selected institution: {BANK_NAME}"
)

print(
    f"Number of bank-level observations: "
    f"{len(bank_data):,}"
)

print(
    f"Reporting periods available: "
    f"{len(periods)}"
)