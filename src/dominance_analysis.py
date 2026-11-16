import pandas as pd


def build_dominance_table(
    df,
    dominance_threshold,
):

    freq = df.reset_index().pivot_table(
        index=["country", "week"],
        columns="variant",
        values="frequency",
        fill_value=0,
    )

    result = freq.assign(
        top_variant=freq.idxmax(axis=1),
        top_frequency=freq.max(axis=1),
    )

    result["dominant_variant"] = result["top_variant"].where(
        result["top_frequency"] >= dominance_threshold
    )

    return result.reset_index()[["country", "week", "dominant_variant"]]


def get_raw_dominance_periods(dominance):
    d = dominance.sort_values(["country", "week"]).copy()

    d["block"] = d.groupby("country")["dominant_variant"].transform(
        lambda s: (s.ne(s.shift())).cumsum()
    )

    d = d[(d["dominant_variant"] != "Not recorded") | (d["block"] == 1)]

    periods = (
        d.dropna(subset=["dominant_variant"])
        .groupby(
            [
                "country",
                "dominant_variant",
                "block",
            ]
        )
        .agg(
            start=("week", "min"),
            end=("week", "max"),
            weeks=("week", "count"),
        )
        .reset_index()
    )

    return periods


def interpolate_dominance_periods(periods, df):

    empty_weeks = set(
        map(
            tuple,
            df.reset_index()
            .query("total == 1 and " "variant == 'Not recorded' and " "count == 1")[
                ["country", "week"]
            ]
            .itertuples(index=False, name=None),
        )
    )

    rows = []

    for (country, variant), g in periods.groupby(["country", "dominant_variant"]):

        g = g.sort_values("start")

        current_start = None
        current_end = None

        for row in g.itertuples():

            if current_start is None:
                current_start = row.start
                current_end = row.end
                continue

            intervening_weeks = pd.date_range(
                current_end + pd.Timedelta(weeks=1),
                row.start - pd.Timedelta(weeks=1),
                freq="7D",
            )

            gap_is_empty = all(
                (country, week) in empty_weeks for week in intervening_weeks
            )

            if gap_is_empty:
                # interpolate across the empty gap
                current_end = row.end
            else:
                # genuine break in dominance
                rows.append(
                    {
                        "country": country,
                        "dominant_variant": variant,
                        "start": current_start,
                        "end": current_end,
                    }
                )

                current_start = row.start
                current_end = row.end

        if current_start is not None:
            rows.append(
                {
                    "country": country,
                    "dominant_variant": variant,
                    "start": current_start,
                    "end": current_end,
                }
            )

    return pd.DataFrame(rows)


def get_dominance_periods(df, dominance_threshold):
    weeks = df.index.get_level_values("week")
    df = df[(weeks >= "2019-12-01") & (weeks <= "2022-12-31")]

    dominance = build_dominance_table(df, dominance_threshold)

    # Remove known Spain artefact
    mask = (
        (dominance["country"] == "Spain")
        & (dominance["week"] == pd.Timestamp("2020-02-09"))
        & (dominance["dominant_variant"] == "VOC Alpha")
    )
    dominance.loc[mask, "dominant_variant"] = "Not recorded"

    periods = get_raw_dominance_periods(dominance)
    interpolated_periods = interpolate_dominance_periods(
        periods,
        df,
    )

    # Extend initial wildtype dominance back to 2019-12-01
    for country in interpolated_periods["country"].unique():
        mask = (interpolated_periods["country"] == country) & (
            interpolated_periods["dominant_variant"] == "Not recorded"
        )
        if mask.any():
            idx = interpolated_periods.loc[mask, "start"].idxmin()
            interpolated_periods.loc[idx, "start"] = pd.Timestamp("2019-12-01")

    return interpolated_periods
