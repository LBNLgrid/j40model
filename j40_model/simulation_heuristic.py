import pandas as pd


def annual_cost(c, r, lt):

    return c * (r / (1 - (1 + r) ** -lt))


def simulation(df, eligible, eb_target,
               cost_table, inv_rate=0.03):

    df = df.copy()
    df_tract = pd.DataFrame(index=df.fips.unique())

    for k in eligible.keys():
        df[k] = 0
        df.loc[eligible[k], k] = 1

    #  weatherization
    df['eld'] = df['annual_elec_cost_dol_per_year'] / df['avg_elec_price_dol_per_kwh'] * (
            1 - df.k_w_el * df.weatherization_savings_per_home)

    df['ec'] = (df.eld * df.avg_elec_price_dol_per_kwh
                + df.annual_gas_cost_dol_per_year * (1 - df.weatherization_savings_per_home * df.k_w_gs)
                + df.annual_fuel_cost_dol_per_year * (1 - df.weatherization_savings_per_home * df.k_w_of))

    df['d_wth'] = df[['k_w_el', 'k_w_gs', 'k_w_of']].sum(axis=1)
    df['C_wth'] = df.d_wth * df.weatherization_cost_per_home * cost_table.loc['weatherization']['cost']
    df['c_wth'] = annual_cost(df.C_wth, inv_rate, cost_table.loc['weatherization']['lifetime'])

    # Calculate DER needs under net-metering conditions based on energy burden
    g = ((df.ec - eb_target * df.annual_income
          ) / df.avg_elec_price_dol_per_kwh).clip(lower=0)
    g = pd.concat([g, df.eld], axis=1).min(axis=1)

    # rts deployment is limited by eligibility and potential
    df['d_rts'] = pd.concat([df.k_rts * g / df.annual_solar_cf,
                             df.solar_kw_potential / df.weight], axis=1).min(axis=1)
    df['g_rts'] = df.d_rts * df.solar_kw_potential
    df['C_rts'] = df['d_rts'] * cost_table.loc['rooftop_solar']['cost']
    df['c_rts'] = annual_cost(df['C_rts'], inv_rate, cost_table.loc['rooftop_solar']['lifetime'])

    # update DER generation needs and net_load
    g = g - df.d_rts * df.g_rts
    net_d = df.eld - df.g_rts

    # Community Solar generation
    # get the max generation per building based on the building with
    # minimum available net load in the tract
    tract = pd.concat([df[['fips', 'k_cs']], net_d, g], axis=1)
    net_g_tract = tract.loc[tract.k_cs == 1].groupby('fips')[0].min()
    g_tract = tract.loc[tract.k_cs == 1].groupby('fips')[1].max()

    df['g_cs'] = df.fips.map(pd.concat([net_g_tract,
                                        g_tract], axis=1).min(axis=1).to_dict()) * df.k_cs

    df_tract['d_cs'] = pd.concat([df.fips, df.g_cs * df.weight / df.annual_solar_cf],
                                 axis=1).groupby('fips').sum()

    df_tract['C_cs'] = df_tract.d_cs * cost_table.loc['community_solar']['cost']
    df_tract['c_cs'] = annual_cost(df_tract.C_cs, inv_rate,
                                   cost_table.loc['community_solar']['lifetime'])

    # update DER generation needs and net_load
    net_d = net_d - df.g_cs

    # Community Wind - repeat the same as for com solar
    # only deploys CW if k_cs =! k_cw
    tract = pd.concat([df[['fips', 'k_cw']], net_d, g], axis=1)
    net_g_tract = tract.loc[tract.k_cw == 1].groupby('fips')[0].min()
    g_tract = tract.loc[tract.k_cw == 1].groupby('fips')[1].max()

    df['g_cw'] = df.fips.map(pd.concat([net_g_tract,
                                        g_tract], axis=1).min(axis=1).to_dict()) * df.k_cw

    df_tract['d_cw'] = pd.concat([df.fips, df.g_cw * df.weight / df.annual_wind_cf],
                                 axis=1).groupby('fips').sum()
    df_tract['C_cw'] = df_tract.d_cw * cost_table.loc['community_wind']['cost']
    df_tract['c_cw'] = annual_cost(df_tract.C_cw, inv_rate,
                                   cost_table.loc['community_wind']['lifetime'])

    df['eg'] = df[['g_rts', 'g_cs', 'g_cw']].sum(axis=1)
    df['eb'] = df['ec']/df.annual_income
    res_bdg = df[['d_wth', 'C_wth', 'c_wth', 'd_rts', 'C_rts',
                  'c_rts', 'g_rts', 'g_cs', 'g_cw', 'ec', 'eld', 'eg', 'eb']]

    return res_bdg, df_tract
