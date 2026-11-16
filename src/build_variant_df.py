import os

import pandas as pd


def parse_variant_sheet(sheet_name, raw_df):

    variant = sheet_name

    dates = pd.to_datetime(raw_df.iloc[0], errors="coerce")
    date_cols = dates[dates.notna()].index

    rows = []
    r = 1

    while r < len(raw_df) - 2:

        country = raw_df.iloc[r, 0]

        if pd.isna(country):
            r += 1
            continue

        country = str(country).strip()

        count_row = r
        total_row = r + 1

        count_label = str(raw_df.iloc[count_row, 1]).strip()
        total_label = str(raw_df.iloc[total_row, 1]).strip()

        if count_label != "count":
            raise ValueError(
                f"{sheet_name}: expected 'count' after "
                f"{country}, found {count_label!r}"
            )

        if total_label != "total":
            raise ValueError(
                f"{sheet_name}: expected 'total' after "
                f"{country}, found {total_label!r}"
            )

        for c in date_cols:
            rows.append(
                {
                    "country": country,
                    "week": dates[c],
                    "variant": variant,
                    "count": (
                        0
                        if pd.isna(raw_df.iloc[count_row, c])
                        else float(raw_df.iloc[count_row, c])
                    ),
                    "total": (
                        np.nan
                        if pd.isna(raw_df.iloc[total_row, c])
                        else float(raw_df.iloc[total_row, c])
                    ),
                }
            )

        r += 2

    return pd.DataFrame(rows)


def excel_import(filename):
    xls = pd.ExcelFile(filename)
    variant_sheets = [s for s in xls.sheet_names if s != "README"]

    dfs = []

    for sheet in variant_sheets:
        raw = xls.parse(sheet, header=None)
        dfs.append(parse_variant_sheet(sheet, raw))

    df = pd.concat(dfs, ignore_index=True)

    return df


def build_out_df(df):
    all_countries = sorted(df["country"].unique())
    all_weeks = sorted(df["week"].unique())
    all_variants = sorted(df["variant"].unique())

    full_index = pd.MultiIndex.from_product(
        [all_countries, all_weeks, all_variants], names=["country", "week", "variant"]
    )

    df = df.set_index(["country", "week", "variant"]).reindex(full_index)

    df["count"] = df["count"].fillna(0)

    group_total = df["total"].groupby(["country", "week"]).transform("max")

    df["total"] = df["total"].fillna(group_total)

    # A significant issue with the data is that wildtype is not a separately documented.
    # Here we set totals to 1 so that if no variants are recorded, we can count "Not recorded" as dominant
    df["total"] = df["total"].fillna(1)

    return df


def add_not_recorded(df):
    known = df.groupby(["country", "week"])["count"].sum()
    totals = df.groupby(["country", "week"])["total"].first()
    not_recorded = (totals - known).clip(lower=0)
    nr = pd.DataFrame({"count": not_recorded, "total": totals})

    nr["variant"] = "Not recorded"

    nr = nr.reset_index().set_index(["country", "week", "variant"])
    df = pd.concat([df, nr])
    return df


def build_df(data_path, filename):
    try:
        df = pd.read_pickle(os.path.join(data_path, "gisaid_tidy_df.pkl"))
        print("Recovered data from cache")
    except:
        df = excel_import(filename)
        df = build_out_df(df)
        df = add_not_recorded(df)
        df["frequency"] = df["count"] / df["total"]
        df.to_pickle(os.path.join(data_path, "gisaid_tidy_df.pkl"))
        print("Cached data")
    return df
