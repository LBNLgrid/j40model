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

from j40_model.simulation_heuristic import simulation
from j40_model.optimization_model import optimization


def interventions_main(df_e, el_sets,
                       energy_burden_target, cost_table, opt=False, **kwargs):

    if opt:
        res_bdg, res_tr = optimization(df_e, el_sets,
                                       energy_burden_target, cost_table, **kwargs)
    else:
        res_bdg, res_tr = simulation(df_e, el_sets,
                                     energy_burden_target, cost_table)

    # get tract results per building and join
    per_bdg = df_e[['fips']].copy()
    for c_gen in ['cs', 'cw']:
        el_per_tract = df_e[['fips', 'weight']].loc[
            el_sets[f'k_{c_gen}']].groupby('fips').sum()
        for lbl in [x for x in res_tr.keys() if c_gen in x]:
            tr_map = res_tr[lbl].div(el_per_tract.weight,
                                     axis=0).fillna(0).to_dict()
            per_bdg[lbl] = per_bdg.fips.map(tr_map)
    per_bdg = res_bdg.join(per_bdg.drop('fips', axis=1))

    return per_bdg, res_tr
