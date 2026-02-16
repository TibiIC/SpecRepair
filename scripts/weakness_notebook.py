# %%
# ===============================================
# SECTION 1 — Imports
# ===============================================
import pandas as pd
import numpy as np

# %%
# ===============================================
# SECTION 2 — Load CSV Once
# ===============================================
CSV_PATH = "scripts/weakness_results/lift_2025-11-19/weakness_table_2.csv"  # <-- edit if needed
case_study_name="Traffic Single"
IS_DEBUG = False

df = pd.read_csv(CSV_PATH)

print("Loaded", len(df), "rows.")

# %%
# ===============================================
# SECTION 2.1 — Rewrite the CSV if it has -inf values
# ===============================================
if (df == -np.inf).any().any():
    print("Replacing -inf with 0 and rewriting CSV...")
    df.replace(-np.inf, 0, inplace=True)
    df.to_csv(CSV_PATH, index=False)
    print("Rewritten.")

# %%
# ===============================================
# SECTION 2.2 — Rewrite the CSV asm_d3 and gar_d3 columns from value to 1 - value
# ===============================================
if "asm_d3" in df.columns and "gar_d3" in df.columns:
    print("Transforming asm_d3 and gar_d3 columns: value -> 1 - value")
    df["asm_d3"] = 1 - df["asm_d3"]
    df["gar_d3"] = 1 - df["gar_d3"]
    print("CSV rewritten with transformed asm_d3 and gar_d3 columns.")
else:
    print("Columns asm_d3 and/or gar_d3 not found in CSV.")

# %%
# ===============================================
# SECTION 3 — Categorize (normal vs ideal/original/trivial)
# ===============================================

normal_df   = df[df["type"] == "normal"].copy()
ideal_df    = df[df["type"] == "ideal"].copy()
original_df = df[df["type"] == "original"].copy()
trivial_df  = df[df["type"] == "trivial"].copy()

print("Normal specs:  ", len(normal_df))
print("Ideal specs:   ", len(ideal_df))
print("Original specs:", len(original_df))
print("Trivial specs: ", len(trivial_df))


# %%
# ===============================================
# SECTION 4 — Utility functions
# ===============================================

def dist_4d(normal_df, ref_row):
    """
    Compute 4D Euclidean distance for ASM vector:
    [asm_d0, asm_d1, asm_d2, asm_d3]
    between each row in normal_df and one reference row.
    """
    dims = ["asm_d0", "asm_d1", "asm_d2", "asm_d3"]

    # reference vector
    ref_vec = ref_row[dims].to_numpy(dtype=float)

    # all normal vectors (N x 4)
    normal_vecs = normal_df[dims].to_numpy(dtype=float)

    # 4D Euclidean: || x - ref ||
    euclid = np.linalg.norm(normal_vecs - ref_vec, axis=1)

    # also return per-dimension differences if needed
    diffs = np.abs(normal_vecs - ref_vec)

    return diffs, euclid

def dist_to_single(normal, ref_row):
    asm_dims = ["asm_d0", "asm_d1", "asm_d3"]
    gar_dims = ["gar_d0", "gar_d1", "gar_d3"]

    # Load
    asm_ref = ref_row[asm_dims].to_numpy(float)
    asm = normal[asm_dims].to_numpy(float)

    gar_ref = ref_row[gar_dims].to_numpy(float)
    gar = normal[gar_dims].to_numpy(float)

    # Identify only the finite dimensions
    finite_asm = np.isfinite(asm_ref)
    finite_gar = np.isfinite(gar_ref)

    # Filter
    asm_ref_f = asm_ref[finite_asm]
    asm_f = asm[:, finite_asm]

    gar_ref_f = gar_ref[finite_gar]
    gar_f = gar[:, finite_gar]

    # Compute Euclidean on filtered dimensions
    asm_dist = np.linalg.norm(asm_f - asm_ref_f, axis=1)
    gar_dist = np.linalg.norm(gar_f - gar_ref_f, axis=1)

    return asm_dist, gar_dist

def dist_to_single_per_dim(normal, ref_row):
    asm_dims = ["asm_d0", "asm_d1", "asm_d3"]
    gar_dims = ["gar_d0", "gar_d1", "gar_d3"]

    asm_ref = ref_row[asm_dims].to_numpy(float)
    asm = normal[asm_dims].to_numpy(float)

    gar_ref = ref_row[gar_dims].to_numpy(float)
    gar = normal[gar_dims].to_numpy(float)

    # Masks of valid dimensions (based on ref)
    finite_asm = np.isfinite(asm_ref)
    finite_gar = np.isfinite(gar_ref)

    # Initialize outputs with NaN (shape: n_rows x 3)
    asm_dist = np.full((asm.shape[0], 3), np.nan)
    gar_dist = np.full((gar.shape[0], 3), np.nan)

    # Compute per-dimension euclidean contribution
    asm_dist[:, finite_asm] = np.sqrt(
        (asm[:, finite_asm] - asm_ref[finite_asm]) ** 2
    )

    gar_dist[:, finite_gar] = np.sqrt(
        (gar[:, finite_gar] - gar_ref[finite_gar]) ** 2
    )

    return asm_dist, gar_dist

def dist_to_single_combined(normal, ref_row):
    """
    Compute the unified Euclidean distance between each normal spec
    and a single reference row across all 8 dimensions.
    """

    # Eight-component feature vector per specification
    dims = [
        "asm_d0", "asm_d1", "asm_d2", "asm_d3",
        "gar_d0", "gar_d1", "gar_d2", "gar_d3"
    ]

    # ref_row[dims] is a pandas Series → (8,)
    # ref is a 1D NumPy array → shape = (8,)
    ref = ref_row[dims].to_numpy(float)      # shape: (8,)

    # normal[dims] is a pandas DataFrame → (N rows, 8 cols)
    # mat is a 2D NumPy array → shape = (N, 8)
    mat = normal[dims].to_numpy(float)       # shape: (N, 8)

    # Boolean mask telling which of the 8 dims are finite
    # finite is 1D → shape = (8,)
    finite = np.isfinite(ref)                # shape: (8,)

    # Keep only the finite coordinates
    # ref_f → shape: (k,) where k = number of finite dimensions
    ref_f = ref[finite]                      # shape: (k,)

    # Filter the columns of mat to keep only finite dims
    # mat_f → shape: (N, k)
    mat_f = mat[:, finite]                   # shape: (N, k)

    # mat_f - ref_f broadcasts:
    #   mat_f (N, k)
    #   ref_f (k,)
    # result: (N, k)
    #
    # Euclidean norm across each row → shape: (N,)
    dist = np.linalg.norm(mat_f - ref_f, axis=1)

    return dist     # shape: (N,)

def dist_to_trivial(normal, trivial):
    """
    Compute min and average distance of every normal spec
    to the set of trivial specs.
    """
    trivial_asm = trivial["asm_d0"].to_numpy()
    trivial_gar = trivial["gar_d0"].to_numpy()

    asm = normal["asm_d0"].to_numpy()[:, None]
    gar = normal["gar_d0"].to_numpy()[:, None]

    asm_dist = np.abs(asm - trivial_asm)
    gar_dist = np.abs(gar - trivial_gar)
    euclid   = np.sqrt((asm - trivial_asm)**2 + (gar - trivial_gar)**2)

    return {
        "asm_min": asm_dist.min(axis=1),
        "asm_mean": asm_dist.mean(axis=1),
        "gar_min": gar_dist.min(axis=1),
        "gar_mean": gar_dist.mean(axis=1),
        "euclid_min": euclid.min(axis=1),
        "euclid_mean": euclid.mean(axis=1),
    }

def relationship_stats(values: np.ndarray, x: float):
    """
    Given all values in a dimension and a reference value x,
    compute how x relates to the distribution.
    """
    values = np.asarray(values, dtype=float)

    bigger = values[values > x]
    smaller = values[values < x]

    count_bigger = len(bigger)
    count_smaller = len(smaller)

    amt_bigger = np.sum(bigger - x)
    amt_smaller = np.sum(x - smaller)

    # Rank and percentile
    rank = np.sum(values <= x)
    percentile = rank / len(values)

    # Dominance (average signed difference)
    dominance = np.mean(values - x)

    return {
        "count_bigger": count_bigger,
        "count_smaller": count_smaller,
        "amount_bigger": amt_bigger,
        "amount_smaller": amt_smaller,
        "net_amount": amt_bigger - amt_smaller,
        "rank": rank,
        "percentile": percentile,
        "dominance": dominance,
    }


def create_latex_table(normal_to_orig, triv_to_orig, case_study_name):
    """Create a LaTeX table showing distance statistics."""
    latex = [
        "\\begin{table}[h]",
        "\\centering",
        "\\begin{tabular}{lllrrrr}",
        "\\toprule",
        "Case Study & Metric & Type & Mean & Min & Max & Std \\\\",
        "\\midrule"
    ]

    # Add normal to original distances
    # Add trivial to original distances
    for i, ((metric, stats_n),(_,stats_t)) in enumerate(zip(normal_to_orig.items(), triv_to_orig.items())):
        latex.append(
            f"{case_study_name if i==0 else ''} & {metric} & Learned to Original & {stats_n['mean']:.3f} & {stats_n['min']:.3f} & {stats_n['max']:.3f} & {stats_n['std']:.3f} \\\\")
        latex.append(
            f"& & Trivial to Original & {stats_t['mean']:.3f} & {stats_t['min']:.3f} & {stats_t['max']:.3f} & {stats_t['std']:.3f} \\\\")
        latex.append("\\midrule")

    latex.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\caption{Distance Statistics Between Specifications}",
        "\\label{tab:distances}",
        "\\end{table}"
    ])

    return "\n".join(latex)


# %%
# ===============================================
# SECTION 5 — Example: Distances to Ideal Spec
# Run/modify freely
# ===============================================

if not ideal_df.empty:
    ideal_row = ideal_df.iloc[0]
    asm_d, gar_d = dist_to_single(normal_df, ideal_row)
    both_d = dist_to_single_combined(normal_df, ideal_row)

    print("\n=== Distances to Ideal ===")
    print("ASM mean:", asm_d.mean(), "max:", asm_d.max(), "min:", asm_d.min(), "std:", asm_d.std())
    print("GAR mean:", gar_d.mean(), "max:", gar_d.max(), "min:", gar_d.min(), "std:", gar_d.std())
    print("BOTH mean:", both_d.mean(), "max:", both_d.max(), "min:", both_d.min(), "std:", both_d.std())
    # print("Euclid mean:", euc_d.mean(), "max:", euc_d.max())
else:
    print("No ideal spec found.")


# %%
# ===============================================
# SECTION 6 — Example: Distances to Original Spec
# ===============================================

if not original_df.empty:
    orig_row = original_df.iloc[0]
    asm_d, gar_d = dist_to_single(trivial_df, orig_row)
    both_d = dist_to_single_combined(trivial_df, orig_row)
    print("\n=== Trivial to Original ===")
    print("ASM mean:", asm_d.mean(), "max:", asm_d.max(), "min:", asm_d.min(), "std:", asm_d.std())
    print("GAR mean:", gar_d.mean(), "max:", gar_d.max(), "min:", gar_d.min(), "std:", gar_d.std())
    print("BOTH mean:", both_d.mean(), "max:", both_d.max(), "min:", both_d.min(), "std:", both_d.std())

    triv_to_orig = {
        "ASM": {"mean": asm_d.mean(), "min": asm_d.min(), "max": asm_d.max(), "std": asm_d.std()},
        "GAR": {"mean": gar_d.mean(), "min": gar_d.min(), "max": gar_d.max(), "std": gar_d.std()},
        "BOTH": {"mean": both_d.mean(), "min": both_d.min(), "max": both_d.max(), "std": both_d.std()}
    }

    asm_d, gar_d = dist_to_single(normal_df, orig_row)
    both_d = dist_to_single_combined(normal_df, orig_row)

    print("\n=== Distances to Original ===")
    print("ASM mean:", asm_d.mean(), "max:", asm_d.max(), "min:", asm_d.min(), "std:", asm_d.std())
    print("GAR mean:", gar_d.mean(), "max:", gar_d.max(), "min:", gar_d.min(), "std:", gar_d.std())
    print("BOTH mean:", both_d.mean(), "max:", both_d.max(), "min:", both_d.min(), "std:", both_d.std())

    normal_to_orig = {
        "ASM": {"mean": asm_d.mean(), "min": asm_d.min(), "max": asm_d.max(), "std": asm_d.std()},
        "GAR": {"mean": gar_d.mean(), "min": gar_d.min(), "max": gar_d.max(), "std": gar_d.std()},
        "BOTH": {"mean": both_d.mean(), "min": both_d.min(), "max": both_d.max(), "std": both_d.std()}
    }

    latex_table = create_latex_table(normal_to_orig, triv_to_orig, case_study_name)
    print("\nLaTeX Table:")
    print(latex_table)
else:
    print("No original spec found.")


# %%
# ===============================================
# SECTION 6.1 — Example: Distances to Original Spec in 3D
# ===============================================

if not original_df.empty:
    orig_row = original_df.iloc[0]
    asm_d, gar_d = dist_to_single_per_dim(trivial_df, orig_row)
    print("\n=== Trivial to Original ===")
    print("ASM mean:", asm_d.mean(axis=0), "max:", asm_d.max(axis=0), "min:", asm_d.min(axis=0), "std:", asm_d.std(axis=0))
    print("GAR mean:", gar_d.mean(axis=0), "max:", gar_d.max(axis=0), "min:", gar_d.min(axis=0), "std:", gar_d.std(axis=0))

    triv_to_orig = {
        "ASM": {"mean": asm_d.mean(axis=0), "min": asm_d.min(axis=0), "max": asm_d.max(axis=0), "std": asm_d.std(axis=0)},
        "GAR": {"mean": gar_d.mean(axis=0), "min": gar_d.min(axis=0), "max": gar_d.max(axis=0), "std": gar_d.std(axis=0)},
    }

    asm_d, gar_d = dist_to_single_per_dim(normal_df, orig_row)

    print("\n=== Distances to Original ===")
    print("ASM mean:", asm_d.mean(axis=0), "max:", asm_d.max(axis=0), "min:", asm_d.min(axis=0), "std:", asm_d.std(axis=0))
    print("GAR mean:", gar_d.mean(axis=0), "max:", gar_d.max(axis=0), "min:", gar_d.min(axis=0), "std:", gar_d.std(axis=0))

    normal_to_orig = {
        "ASM": {"mean": asm_d.mean(axis=0), "min": asm_d.min(axis=0), "max": asm_d.max(axis=0), "std": asm_d.std(axis=0)},
        "GAR": {"mean": gar_d.mean(axis=0), "min": gar_d.min(axis=0), "max": gar_d.max(axis=0), "std": gar_d.std(axis=0)},
    }

    latex_table = create_latex_table(normal_to_orig, triv_to_orig, case_study_name)
    print("\nLaTeX Table:")
    print(latex_table)
else:
    print("No original spec found.")

# %%
# ===============================================
# SECTION 6.2 — Generate new dfs out of original, trivial & normal, where asm_d0 and asm_d3 are multiplied into a new column, and similarly for gar_d0 and gar_d3
# ===============================================

def create_merged_df(df):
    """
    Create a new dataframe with merged asm_d0,asm_d1,asm_d3 and gar_d0,gar_d1,gar_d3 as new columns.
    """
    eps = 1e-12
    lexicographic_distance = 1
    new_df = df.copy()


    # Assert all entries in asm_d0 and asm_d3 are between 0 and 1 inclusive
    assert new_df['asm_d0'].between(-eps, 1 + eps).all(), "asm_d0 contains values outside [0, 1]"
    assert new_df['asm_d1'].between(-eps, 1 + eps).all(), "asm_d1 contains values outside [0, 1]"
    assert new_df['asm_d3'].between(-eps, 1 + eps).all(), "asm_d3 contains values outside [0, 1]"
    assert new_df['gar_d0'].between(-eps, 1 + eps).all(), "gar_d0 contains values outside [0, 1]"
    assert new_df['gar_d1'].between(-eps, 1 + eps).all(), "gar_d1 contains values outside [0, 1]"
    assert new_df['gar_d3'].between(-eps, 1 + eps).all(), "gar_d3 contains values outside [0, 1]"

    new_df['asm_merged'] = (new_df['asm_d0'] * (10**(lexicographic_distance * 2)) + new_df['asm_d1'] * (10**lexicographic_distance) + new_df['asm_d3']) / (10**(lexicographic_distance * 2) + 10**lexicographic_distance + 1)
    new_df['gar_merged'] = (new_df['gar_d0'] * (10**(lexicographic_distance * 2)) + new_df['gar_d1'] * (10**lexicographic_distance) + new_df['gar_d3']) / (10**(lexicographic_distance * 2) + 10**lexicographic_distance + 1)
    return new_df


# Generate new dataframes with multiplied columns
normal_mult_df = create_merged_df(normal_df)
trivial_mult_df = create_merged_df(trivial_df)
original_mult_df = create_merged_df(original_df)

print("\n=== Multiplied DataFrames Created ===")
print(f"Normal (multiplied):   {len(normal_mult_df)} rows, columns: {list(normal_mult_df.columns)}")
print(f"Trivial (multiplied):  {len(trivial_mult_df)} rows, columns: {list(trivial_mult_df.columns)}")
print(f"Original (multiplied): {len(original_mult_df)} rows, columns: {list(original_mult_df.columns)}")

# Display sample statistics
print("\n=== Sample Statistics (Original) ===")
print(f"asm_merged: mean={original_mult_df['asm_merged'].mean():.4f}, "
      f"min={original_mult_df['asm_merged'].min():.4f}, "
      f"max={original_mult_df['asm_merged'].max():.4f}, "
      f"std={original_mult_df['asm_merged'].std():.4f}")
print(f"gar_merged: mean={original_mult_df['gar_merged'].mean():.4f}, "
      f"min={original_mult_df['gar_merged'].min():.4f}, "
      f"max={original_mult_df['gar_merged'].max():.4f}, "
      f"std={original_mult_df['gar_merged'].std():.4f}")
print("\n=== Sample Statistics (Trivial) ===")
print(f"asm_merged: mean={trivial_mult_df['asm_merged'].mean():.4f}, "
      f"min={trivial_mult_df['asm_merged'].min():.4f}, "
      f"max={trivial_mult_df['asm_merged'].max():.4f}, "
      f"std={trivial_mult_df['asm_merged'].std():.4f}")
print(f"gar_merged: mean={trivial_mult_df['gar_merged'].mean():.4f}, "
      f"min={trivial_mult_df['gar_merged'].min():.4f}, "
      f"max={trivial_mult_df['gar_merged'].max():.4f}, "
      f"std={trivial_mult_df['gar_merged'].std():.4f}")
print("\n=== Sample Statistics (Normal) ===")
print(f"asm_merged: mean={normal_mult_df['asm_merged'].mean():.4f}, "
      f"min={normal_mult_df['asm_merged'].min():.4f}, "
      f"max={normal_mult_df['asm_merged'].max():.4f}, "
      f"std={normal_mult_df['asm_merged'].std():.4f}")
print(f"gar_merged: mean={normal_mult_df['gar_merged'].mean():.4f}, "
      f"min={normal_mult_df['gar_merged'].min():.4f}, "
      f"max={normal_mult_df['gar_merged'].max():.4f}, "
      f"std={normal_mult_df['gar_merged'].std():.4f}")

# ===============================================
# Difference statistics between normal and original
# ===============================================

if not original_mult_df.empty:
    orig_mult_row = original_mult_df.iloc[0]

    # Calculate differences for asm_merged
    asm_diff = np.abs(normal_mult_df['asm_merged'].to_numpy() - orig_mult_row['asm_merged'])

    # Calculate differences for gar_merged
    gar_diff = np.abs(normal_mult_df['gar_merged'].to_numpy() - orig_mult_row['gar_merged'])

    # Calculate difference for both using euclidean distance
    both_diff = np.linalg.norm(normal_mult_df[['asm_merged', 'gar_merged']].to_numpy(dtype=float) - orig_mult_row[['asm_merged', 'gar_merged']].to_numpy(dtype=float).reshape(1, 2), axis=1)

    print("\n=== Difference Statistics (Normal vs Original) ===")
    print(f"asm_merged difference: mean={asm_diff.mean():.4f}, "
          f"min={asm_diff.min():.4f}, "
          f"max={asm_diff.max():.4f}, "
          f"std={asm_diff.std():.4f}")
    print(f"gar_merged difference: mean={gar_diff.mean():.4f}, "
          f"min={gar_diff.min():.4f}, "
          f"max={gar_diff.max():.4f}, "
          f"std={gar_diff.std():.4f}")
    print(f"both_diff difference: mean={both_diff.mean():.4f}, "
          f"min={both_diff.min():.4f}, "
          f"max={both_diff.max():.4f}, "
          f"std={both_diff.std():.4f}")

    normal_to_orig = {
        "ASM": {"mean": asm_diff.mean(axis=0), "min": asm_diff.min(axis=0), "max": asm_diff.max(axis=0), "std": asm_diff.std(axis=0)},
        "GAR": {"mean": gar_diff.mean(axis=0), "min": gar_diff.min(axis=0), "max": gar_diff.max(axis=0), "std": gar_diff.std(axis=0)},
        "BOTH": {"mean": both_diff.mean(axis=0), "min": both_diff.min(axis=0), "max": both_diff.max(axis=0), "std": both_diff.std(axis=0)},
    }


    # Find rows where gar_diff is maximum
    if IS_DEBUG:
        max_gar_diff = gar_diff.max()
        max_gar_indices = np.where(gar_diff == max_gar_diff)[0]
        print(f"\nRows with maximum gar_diff ({max_gar_diff:.4f}):")
        for idx in max_gar_indices:
            print(f"  {normal_mult_df.iloc[idx]['filename']}")

    # Calculate differences for asm_merged
    asm_diff = np.abs(trivial_mult_df['asm_merged'].to_numpy() - orig_mult_row['asm_merged'])

    # Calculate differences for gar_merged
    gar_diff = np.abs(trivial_mult_df['gar_merged'].to_numpy() - orig_mult_row['gar_merged'])

    # Calculate difference for both using euclidean distance
    both_diff = np.linalg.norm(trivial_mult_df[['asm_merged', 'gar_merged']].to_numpy(dtype=float) - orig_mult_row[['asm_merged', 'gar_merged']].to_numpy(dtype=float).reshape(1, 2), axis=1)

    print("\n=== Difference Statistics (Trivial vs Original) ===")
    print(f"asm_merged difference: mean={asm_diff.mean():.4f}, "
          f"min={asm_diff.min():.4f}, "
          f"max={asm_diff.max():.4f}, "
          f"std={asm_diff.std():.4f}")
    print(f"gar_merged difference: mean={gar_diff.mean():.4f}, "
          f"min={gar_diff.min():.4f}, "
          f"max={gar_diff.max():.4f}, "
          f"std={gar_diff.std():.4f}")
    print(f"both_diff difference: mean={both_diff.mean():.4f}, "
          f"min={both_diff.min():.4f}, "
          f"max={both_diff.max():.4f}, "
          f"std={both_diff.std():.4f}")

    triv_to_orig = {
        "ASM": {"mean": asm_diff.mean(axis=0), "min": asm_diff.min(axis=0), "max": asm_diff.max(axis=0), "std": asm_diff.std(axis=0)},
        "GAR": {"mean": gar_diff.mean(axis=0), "min": gar_diff.min(axis=0), "max": gar_diff.max(axis=0), "std": gar_diff.std(axis=0)},
        "BOTH": {"mean": both_diff.mean(axis=0), "min": both_diff.min(axis=0), "max": both_diff.max(axis=0), "std": both_diff.std(axis=0)},
    }

    latex_table = create_latex_table(normal_to_orig, triv_to_orig, case_study_name)
    print("\nLaTeX Table:")
    print(latex_table)

    # Find rows where gar_diff is maximum
    if IS_DEBUG:
        max_gar_diff = gar_diff.max()
        max_gar_indices = np.where(gar_diff == max_gar_diff)[0]
        print(f"\nRows with maximum gar_diff ({max_gar_diff:.4f}):")
        for idx in max_gar_indices:
            print(f"  {trivial_mult_df.iloc[idx]['filename']}")
else:
    print("\n=== No original spec found for difference calculation ===")



# ===============================================


# %%
# ===============================================
# SECTION 7 — Example: Distances to Trivial Specs
# ===============================================

if not trivial_df.empty:
    stats = dist_to_trivial(normal_df, trivial_df)

    print("\n=== Distances to Trivial Specs ===")
    for key, arr in stats.items():
        print(f"{key:12} : mean={arr.mean():.6f}, max={arr.max():.6f}")
else:
    print("No trivial specs.")


# %%
# ===============================================
# SECTION 8 — PLAYGROUND AREA
# Add any experiments here (scatter plots, histograms, etc.)
# ===============================================
asm_vals = normal_df["asm_d0"].to_numpy()
ref_asm = ideal_df["asm_d0"].iloc[0]

stats = relationship_stats(asm_vals, ref_asm)
for k, v in stats.items():
    print(f"{k}: {v}")


# %%
# ===============================================
# SECTION 9 — PLOTTING UTIL AREA
# Any helper functions for plotting go here
# ===============================================
import matplotlib.pyplot as plt
from matplotlib.markers import MarkerStyle
import numpy as np
from collections import Counter


def plot_multi_scatter(
    datasets,
    dimension="d0",
    figsize=(12, 9),
    base_marker_sizes=None,
    title=None
):
    """
    Plot multiple weakness datasets in 2D (asm_dX vs gar_dX),
    with overlapping markers and combined label text.

    Parameters
    ----------
    datasets : list of dicts
        Each dict must contain:
            {
                "df": pandas DataFrame,
                "label": str,
                "color": str,
                "marker": str              # e.g. "*", "s", "D", "o"
            }
        The df must contain columns:
            asm_d0 ... asm_d3
            gar_d0 ... gar_d3

    dimension : str
        One of {"d0","d1","d2","d3"}; chooses asm_dX + gar_dX

    base_marker_sizes : dict or None
        Example:
        {
            "*" : 5000,
            "s" : 2800,
            "D" : 2200,
            "o" : 1800
        }
        If None, defaults will be used.

    title : str
        Optional plot title
    """

    # ----------------------------------------------------
    # Normalized access to dimension's columns
    # ----------------------------------------------------
    asm_col = f"asm_{dimension}"
    gar_col = f"gar_{dimension}"

    # ----------------------------------------------------
    # Default marker sizes (from largest to smallest)
    # ----------------------------------------------------
    if base_marker_sizes is None:
        base_marker_sizes = {
            "*": 5000,
            "s": 1000,
            "D": 800,
            "o": 500
        }

    # ----------------------------------------------------
    # Create the figure (NO constrained_layout)
    # ----------------------------------------------------
    fig, ax = plt.subplots(figsize=figsize)

    # ----------------------------------------------------
    # Combine all points into a single grid: (x, y) → list of contributions
    # ----------------------------------------------------
    big_map = {}  # (x,y) -> { label1: count, label2: count, ... }

    # Track plotting info for layering
    layering_list = []  # each entry: (marker_size, df, label, color, marker)

    for entry in datasets:
        df = entry["df"]
        label = entry["label"]
        color = entry["color"]
        marker = entry["marker"]

        if marker not in base_marker_sizes:
            raise ValueError(f"Marker '{marker}' has no size defined.")

        layering_list.append((base_marker_sizes[marker], df, label, color, marker))

        # Insert points into combined map
        for _, row in df.iterrows():
            x = row[asm_col]
            y = row[gar_col]
            key = (x, y)
            if key not in big_map:
                big_map[key] = {}
            big_map[key][label] = big_map[key].get(label, 0) + 1

    # ----------------------------------------------------
    # Sort layers: largest marker drawn first (back), smallest last (front)
    # ----------------------------------------------------
    layering_list.sort(key=lambda x: -x[0])

    # ----------------------------------------------------
    # Draw all points
    # ----------------------------------------------------
    for msize, df, label, color, marker in layering_list:
        ax.scatter(
            df[asm_col],
            df[gar_col],
            s=msize,
            marker=marker,
            color=color,
            edgecolor="black",
            linewidth=1.3,
            zorder=2
        )

    # ----------------------------------------------------
    # Add label text BELOW the largest symbol at each (x, y)
    # ----------------------------------------------------
    for (x, y), label_dict in big_map.items():
        # Pick the *largest marker size* among the types present
        present_sizes = [
            base_marker_sizes[e["marker"]]
            for e in datasets
            if e["label"] in label_dict
        ]
        largest_size = max(present_sizes)
        largest_marker_radius = np.sqrt(largest_size) / 2.0

        # Text to show, e.g. "ideal:1  trivial:3"
        text = "  ".join(f"{lab}:{cnt}" for lab, cnt in label_dict.items())

        # Convert symbol size to data offset
        trans = ax.transData.transform
        inv = ax.transData.inverted().transform

        # Compute downward text offset in data units
        # approx: radius in pixels multiplied by a scale factor
        px_down = largest_marker_radius * 1.1
        x_px, y_px = trans((x, y))
        x2, y2 = inv((x_px, y_px - px_down))

        ax.text(
            x2,
            y2,
            text,
            ha='center',
            va='top',
            fontsize=10,
            fontweight="bold",
            color="black",
            bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.15", alpha=0.8),
            zorder=10
        )

    # ----------------------------------------------------
    # Final styling
    # ----------------------------------------------------
    ax.set_xlabel(f"Assumption Weakness ({asm_col})", fontsize=14)
    ax.set_ylabel(f"Guarantee Weakness ({gar_col})", fontsize=14)

    if title:
        ax.set_title(title, fontsize=16)

    ax.grid(True, linestyle="--", alpha=0.6)

    # ----------------------------------------------------
    # Manual layout padding (works in PyCharm)
    # ----------------------------------------------------
    fig.subplots_adjust(bottom=0.20)

    return fig, ax

# %%
# ===============================================
# SECTION 10 — PLOTTING AREA
# Plot any graphs here (scatter plots, histograms, etc.)
# ===============================================
dimension = "merged"
fig, ax = plot_multi_scatter(
    datasets=[
        {
            "df": normal_mult_df,
            "label": "normal",
            "color": "skyblue",
            "marker": "o",
        },
#       {
#           "df": ideal_df,
#           "label": "ideal",
#           "color": "green",
#           "marker": "*",
#       },
        {
            "df": original_mult_df,
            "label": "original",
            "color": "red",
            "marker": "s",
        },
        {
            "df": trivial_mult_df,
            "label": "trivial",
            "color": "navy",
            "marker": "D",
        },
    ],
    dimension=dimension,  # or d0 / d1 / d2 / d3
    title=f"Weakness Scatter — {dimension}"
)

plt.show()

# %%
# Example: print the closest 10 specs to the ideal
if not ideal_df.empty:
    ideal_row = ideal_df.iloc[0]
    _, _, euc_d = dist_to_single(normal_df, ideal_row)
    normal_df["dist_to_ideal"] = euc_d
    print("\nClosest 10 specs to ideal:")
    print(normal_df.sort_values("dist_to_ideal").head(10)[["filename", "dist_to_ideal"]])

# You can add customizable analysis here.