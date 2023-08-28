def data_corrections(df):
    """
    This method contains ad-hoc corrections to the community file
    ideally those corrections should be integrated in new versions of the community file
    """
    df['weight'].fillna(0, inplace=True)
    df = df[(df['annual_elec_cost_dol_per_year'] + df['annual_gas_cost_dol_per_year']
             + df['annual_fuel_cost_dol_per_year']) < 0.5 * df['annual_income']].copy()
    df.annual_wind_cf *= 8760

    # income target eligibility
    df['baseline_ec'] = df[['annual_elec_cost_dol_per_year', 'annual_gas_cost_dol_per_year',
                            'annual_fuel_cost_dol_per_year']].sum(axis=1)
    df['baseline_eb'] = df['baseline_ec'] / df['annual_income']

    return df


def aggregate_per_tract(df, summed_keys, weighted_keys):
    all_keys = summed_keys + weighted_keys

    w_df = df[['fips', 'weight']].copy()
    for k in all_keys:
        w_df[k] = df[k] * df.weight
    tw_df = w_df.groupby('fips').sum()

    for k in weighted_keys:
        tw_df[k] = tw_df[k] / tw_df.weight

    return tw_df[all_keys + ['weight']]


def eb_percentage(df):
    for col in [c for c in df.columns if 'burden' in c.lower()]:
        df[col +' (%)'] = df[col] * 100.0
    return df
