col_map_base = {
                'state': 'Sate Initials',
                'fips': 'Tract #',
                'weight': '# of Households',
                'tenure': 'Tenure',
                'year_built': 'Year Built',
                'ami': 'AMI Level (%)',
                'baseline_ec': 'Baseline Annual Energy Bill ($)',
                'baseline_eb': 'Baseline Energy Burden'
                }

col_map_results = {'d_wth': '# Buildings Weatherized',
                   'C_wth': 'Weatherization Investments ($)',
                   'c_wth': 'Weatherization Annualized Investments ($)',
                   'd_rts': 'Rooftop Solar Deployment (kW)',
                   'C_rts': 'Rooftop Solar Investments ($)',
                   'c_rts': 'Rooftop Solar Annualized Investments ($)',
                   'g_rts': 'Generation Rooftop Solar (kWh)',
                   'g_cs': 'Generation Community Solar (kWh)',
                   'g_cw': 'Generation Community Wind (kWh)',
                   'ec': 'Energy Bill After Intervention ($)',
                   'eb': 'Energy Burden After Intervention',
                   'd_cs': 'Community Solar Deployment (kW)',
                   'C_cs': 'Community Solar Investments ($)',
                   'c_cs': 'Community Solar Annualized Investments ($)',
                   'd_cw': 'Community Wind Deployment (kW)',
                   'C_cw': 'Community Wind Investments ($)',
                   'c_cw': 'Community Wind Annualized Investments ($)',
                   'solar_kw_potential': 'Rooftop Solar Potential (kW)',
                   'wind_kw_potential': 'Community Wind Potential (kW)',
                   'jobs_per_home': 'Jobs per Home Weatherized',
                   }
col_map_results.update(col_map_base)
