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
CSV_PATH = "scripts/weakness_results/minepump_2025-11-19/weakness_table.csv"  # <-- edit if needed

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
    asm_dims = ["asm_d0", "asm_d1", "asm_d2", "asm_d3"]
    gar_dims = ["gar_d0", "gar_d1", "gar_d2", "gar_d3"]

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

# %%
# ===============================================
# SECTION 5 — Example: Distances to Ideal Spec
# Run/modify freely
# ===============================================

if not ideal_df.empty:
    ideal_row = ideal_df.iloc[0]
    asm_d, gar_d = dist_to_single(normal_df, ideal_row)

    print("\n=== Distances to Ideal ===")
    print("ASM mean:", asm_d.mean(), "max:", asm_d.max())
    print("GAR mean:", gar_d.mean(), "max:", gar_d.max())
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
    print("ASM mean:", asm_d.mean(), "max:", asm_d.max(), "min:", asm_d.min())
    print("GAR mean:", gar_d.mean(), "max:", gar_d.max(), "min:", gar_d.min())
    print("BOTH mean:", both_d.mean(), "max:", both_d.max(), "min:", both_d.min())
    # print("Euclid mean:", euc_d.mean(), "max:", euc_d.max())

    asm_d, gar_d = dist_to_single(normal_df, orig_row)
    both_d = dist_to_single_combined(normal_df, orig_row)

    print("\n=== Distances to Original ===")
    print("ASM mean:", asm_d.mean(), "max:", asm_d.max(), "min:", asm_d.min())
    print("GAR mean:", gar_d.mean(), "max:", gar_d.max(), "min:", gar_d.min())
    print("BOTH mean:", both_d.mean(), "max:", both_d.max(), "min:", both_d.min())
else:
    print("No original spec found.")


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
dimension = "d0"
fig, ax = plot_multi_scatter(
    datasets=[
        {
            "df": normal_df,
            "label": "normal",
            "color": "skyblue",
            "marker": "o",
        },
        {
            "df": ideal_df,
            "label": "ideal",
            "color": "green",
            "marker": "*",
        },
        {
            "df": original_df,
            "label": "original",
            "color": "red",
            "marker": "s",
        },
        {
            "df": trivial_df,
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