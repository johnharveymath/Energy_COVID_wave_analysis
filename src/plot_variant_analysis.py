import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


def get_variant_colors(variants):

    colors = VARIANT_COLORS.copy()

    used_colors = set(colors.values())

    default_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    available_colors = [
        c for c in default_colors
        if c not in used_colors
    ]

    missing = sorted(
        set(variants) - set(colors)
    )

    for i, variant in enumerate(missing):
        colors[variant] = available_colors[i % len(available_colors)]

    return colors
    

def plot_dominance(
    ax, country, periods, variant_colors, cutoff_date, patient_list=None
):
    periods_country = periods[periods["country"] == country]

    for variant, group in periods_country.groupby("dominant_variant"):
        ax.broken_barh(
            list(
                zip(
                    group["start"],
                    group["end"] - group["start"],
                )
            ),
            (-0.25, 0.5),
            facecolors=variant_colors[variant],
        )

    if patient_list is not None:
        country_visits = patient_list[patient_list["Country"] == country].copy()
        country_visits = country_visits[country_visits["plot_date"] <= cutoff_date]
        ax.scatter(
            country_visits["plot_date"],
            np.zeros(len(country_visits)),
            marker="x",
            s=40,
            c="black",
            linewidths=1.5,
            zorder=10,
        )

    ax.set_yticks([])
    ax.set_xlim(pd.Timestamp("2019-11-25"), cutoff_date)


def plot_country(
    country,
    df,
    periods,
    cutoff_date,
    plot_threshold=0.1,
    patient_list=None,
):
    

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 5), sharex=True, gridspec_kw={"height_ratios": [4, 1]}
    )

    country_df = df.loc[country].reset_index()

    plot_df = country_df.pivot(index="week", columns="variant", values="frequency")
    plot_df = plot_df.loc[plot_df.index <= cutoff_date]
    plot_df = plot_df.loc[:, (plot_df.max() > plot_threshold)]

    PLOT_ORDER = [
        "Not recorded",
        "VOC Alpha",
        "VOC Gamma",
        "VOC Delta",
        "VOC Omicron",
    ]

    priority = [v for v in PLOT_ORDER if v in plot_df.columns]
    other_variants = sorted([v for v in plot_df.columns if v not in PLOT_ORDER])
    plot_df = plot_df[priority + other_variants]

    variant_colors = get_variant_colors(
        plot_df.columns
    )
    plot_colors = [variant_colors[v] for v in plot_df.columns]

    ax1.stackplot(
        plot_df.index,
        plot_df.T,
        labels=plot_df.columns,
        colors=plot_colors,
    )
    ax1.set_xlim(right=cutoff_date)
    ax1.set_ylim(0, 1)
    ax1.set_ylabel("Variant frequency")
    ax1.set_title(country)

    ax1.grid(axis="y", alpha=0.3)

    ax1.legend(
        title="Variant",
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
    )

    plot_dominance(ax2, country, periods, variant_colors, cutoff_date, patient_list)
    ax2.set_xlim(right=cutoff_date)

    plt.tight_layout()

    return fig


def plot_all_dominance(periods, countries, cutoff_date, patient_list):
    fig, axes = plt.subplots(
        len(countries),
        1,
        figsize=(12, 0.8 * len(countries)),
        sharex=True,
    )

    variant_colors = get_variant_colors(
        periods["dominant_variant"].dropna().unique()
    )

    countries = np.sort(countries)

    for ax, country in zip(axes, countries):
        plot_dominance(ax, country, periods, variant_colors, cutoff_date, patient_list)

        ax.set_ylabel(
            country,
            rotation=0,
            ha="right",
            va="center",
        )
        ax.set_xlim(right=cutoff_date)

    axes[0].tick_params(
        axis="x",
        top=True,
        labeltop=True,
    )

    legend_handles = [
        Patch(
            facecolor=color,
            label=(
                "Wildtype" if variant == "Not recorded" else variant.replace("VOC ", "")
            ),
        )
        for variant, color in variant_colors.items()
    ]

    fig.suptitle(
        "Dominant SARS-CoV-2 variants and symptom onset dates for participants",
        fontsize=16,
        y=0.99,
    )

    fig.legend(
        handles=legend_handles,
        ncol=len(legend_handles),
        loc="upper center",
        bbox_to_anchor=(0.5, 0.97),
    )

    fig.subplots_adjust(
        top=0.935,
        left=0.10,
        right=0.98,
        hspace=0.3,
    )

    return fig


VARIANT_COLORS = {
    "Not recorded": "#9467bd",  # purple
    "VOC Alpha": "#1f77b4",  # blue
    "VOC Gamma": "#2ca02c",  # green
    "VOC Delta": "#ff7f0e",  # orange
    "VOC Omicron": "#d62728",  # red
}
