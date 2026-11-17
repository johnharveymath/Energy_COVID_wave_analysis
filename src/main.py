import os

import pandas as pd
import matplotlib.pyplot as plt

from config import Config
from plot_variant_analysis import plot_country, plot_all_dominance
from build_variant_df import build_df
from dominance_analysis import get_dominance_periods

if __name__ == "__main__":

    CONFIG = Config(os.path.dirname(os.path.realpath(__file__)))
    FILENAME = os.path.join(
        CONFIG.data_path, "gisaid_variants_statistics_2025_01_19_1130.xlsx"
    )
    DOMINANCE_THRESHOLD = 0.65
    CUTOFF_DATE = pd.Timestamp("2022-12-31")

    df = build_df(CONFIG.data_path, FILENAME)
    periods = get_dominance_periods(df, DOMINANCE_THRESHOLD)

    patient_list = pd.read_csv(os.path.join(CONFIG.data_path, "patient_list.csv"))
    energy_countries = patient_list["Country"].unique()
    gisaid_countries = sorted(df.index.get_level_values("country").unique())

    for country in energy_countries:
        if country not in gisaid_countries:
            raise ValueError(f"{country} not found in GISAID data")

    periods[periods["country"].isin(energy_countries)].to_csv(
        os.path.join(
            CONFIG.plot_path, f"dominance_periods_{int(DOMINANCE_THRESHOLD * 100)}.csv"
        )
    )

    patient_list["date_covid_onset"] = pd.to_datetime(
        patient_list["date_covid_onset"], format="%d/%m/%Y"
    )
    patient_list["visit_date"] = pd.to_datetime(
        patient_list["visit_date"], format="%d/%m/%Y"
    )
    patient_list["plot_date"] = patient_list["date_covid_onset"].where(
        patient_list["date_covid_onset"].dt.year != 2001,
        patient_list["visit_date"],
    )

    for country in energy_countries:
        fig = plot_country(country, df, periods, CUTOFF_DATE, patient_list=patient_list)
        fig.savefig(
            os.path.join(CONFIG.plot_path, f"{country}_variants.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close(fig)

    fig = plot_all_dominance(periods, energy_countries, CUTOFF_DATE, patient_list)
    fig.savefig(
        os.path.join(CONFIG.plot_path, "all_dominance.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)
