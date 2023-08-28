"""
*** Copyright Notice ***

Justice 40 Tool (J40 Tool) Copyright (c) 2023, The Regents of the University
of California, through Lawrence Berkeley National Laboratory (subject to receipt ofany required approvals from the U.S.
Dept. of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Intellectual Property Office at
IPO@lbl.gov.

NOTICE.  This Software was developed under funding from the U.S. Department
of Energy and the U.S. Government consequently retains certain rights.  As
such, the U.S. Government has been granted for itself and others acting on
its behalf a paid-up, nonexclusive, irrevocable, worldwide license in the
Software to reproduce, distribute copies to the public, prepare derivative
works, and perform publicly and display publicly, and to permit others to do so.
"""

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
