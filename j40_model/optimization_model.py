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

import pandas as pd
from pyomo.environ import *
from pyomo.opt import SolverFactory


def total_cost_cost(c, r, lt):

    return c / (r / (1 - (1 + r) ** -lt))


def optimization(df, eligible, eb_target, cost_table, **kwargs):

    if kwargs:
        inv_rate = kwargs['inv_rate']
        eb_weight = kwargs['eb_weight']
        budget_limit = kwargs['budget_limit']
        solver = kwargs['solver']

    else:
        inv_rate = 0.03
        eb_weight = 1
        budget_limit = 1e10
        solver = 'cplex'

    m = ConcreteModel()

    print('writing model', solver)
    # sets
    m.k_rts = Set(initialize=eligible['k_rts'])
    m.k_cs = Set(initialize=eligible['k_cs'])
    m.k_cw = Set(initialize=eligible['k_cw'])

    m.k_w_el = Set(initialize=eligible['k_w_el'])
    m.k_w_gs = Set(initialize=eligible['k_w_gs'])
    m.k_w_of = Set(initialize=eligible['k_w_of'])
    m.k_w = m.k_w_el | m.k_w_gs | m.k_w_of

    m.k = Set(initialize=df.index.to_list())
    m.T = Set(initialize=df.loc[m.k]['fips'].unique())
    m.Tk_cs = Set(m.T, initialize=df.loc[m.k_cs].reset_index()[
        ['fips', 'index']].groupby('fips')['index'].apply(list).to_dict())
    m.Tk_cw = Set(m.T, initialize=df.loc[m.k_cw].reset_index()[
        ['fips', 'index']].groupby('fips')['index'].apply(list).to_dict())

    m.Tk_cg = Set(m.T, initialize=df.loc[m.k_cs | m.k_cw].reset_index()[
        ['fips', 'index']].groupby('fips')['index'].apply(list).to_dict())

    # params
    m.WS = Param(m.k_w, initialize=df.loc[m.k_w]['weatherization_savings_per_home'].to_dict())
    m.rts_prod = Param(m.k_rts, initialize=df.loc[m.k_rts]['annual_solar_cf'].to_dict())
    m.cs_prod = Param(m.k_cs, initialize=df.loc[m.k_cs]['annual_solar_cf'].to_dict())
    m.wnd_prod = Param(m.k_cw, initialize=(df.loc[m.k_cw]['annual_wind_cf']).to_dict())

    m.cw_max_kw = Param(m.k_cw, initialize=(df.loc[m.k_cw]['wind_kw_potential']).to_dict())
    m.rts_max_kw = Param(m.k_rts, initialize=df.loc[m.k_rts]['solar_kw_potential'].to_dict())

    m.n_bdg = Param(m.k, initialize=df.loc[m.k]['weight'].to_dict())
    m.income = Param(m.k, initialize=df.loc[m.k]['annual_income'].to_dict())

    m.C_rts = Param(initialize=cost_table.loc['rooftop_solar']['cost'])
    m.C_cs = Param(initialize=cost_table.loc['community_solar']['cost'])
    m.C_cw = Param(initialize=cost_table.loc['community_wind']['cost'])
    m.C_wth = Param(m.k_w, initialize=(df.loc[m.k_w]['weatherization_cost_per_home'] *
                                       cost_table.loc['weatherization']['cost']).to_dict())

    m.Lt_rts = Param(initialize=cost_table.loc['rooftop_solar']['lifetime'])
    m.Lt_cs = Param(initialize=cost_table.loc['community_solar']['lifetime'])
    m.Lt_cw = Param(initialize=cost_table.loc['community_wind']['lifetime'])
    m.Lt_wth = Param(initialize=cost_table.loc['weatherization']['lifetime'])

    m.C_el = Param(m.k, initialize=df.loc[m.k]['annual_elec_cost_dol_per_year'].to_dict())
    m.C_gs = Param(m.k, initialize=df.loc[m.k]['annual_gas_cost_dol_per_year'].to_dict())
    m.C_of = Param(m.k, initialize=df.loc[m.k]['annual_fuel_cost_dol_per_year'].to_dict())

    m.P_el = Param(m.k, initialize=df.loc[m.k]['avg_elec_price_dol_per_kwh'].to_dict())
    m.R = Param(initialize=inv_rate)

    m.kcs_t = Param(m.k_cs, initialize=df.loc[m.k_cs]['fips'].to_dict())
    m.kcw_t = Param(m.k_cw, initialize=df.loc[m.k_cw]['fips'].to_dict())

    # vars
    m.d_wth = Var(m.k_w, domain=NonNegativeReals)  # number of buildings weatherized
    m.d_rts = Var(m.k_rts, domain=NonNegativeReals)  # MW of solar per building deployed
    m.d_cs = Var(m.T, domain=NonNegativeReals)  # MW deployed in the track
    m.d_cw = Var(m.T, domain=NonNegativeReals)  # MW deployed in the track

    m.g_rts = Var(m.k, domain=NonNegativeReals)  # MWh rooftop generation per building
    m.g_cs = Var(m.k, domain=NonNegativeReals)  # MWh community solar generation
    m.g_cw = Var(m.k, domain=NonNegativeReals)  # MWh community wind generation

    m.c_rts = Var(m.k_rts, domain=NonNegativeReals)  # Annualized costs of solar per building
    m.c_cs = Var(m.T, domain=NonNegativeReals)  # Annualized costs of community solar per tract
    m.c_cw = Var(m.T, domain=NonNegativeReals)  # Annualized costs of community wind per tract
    m.c_wth = Var(m.k_w, domain=NonNegativeReals)  # Annualized costs of weatherization per building
    m.nel_tract = Var(m.T, domain=Reals)  # Net-load tract

    m.eld = Var(m.k, domain=NonNegativeReals)  # electricity demand per building kwh
    m.nel = Var(m.k, domain=Reals)  # net electricity demand per building kWh
    m.ec = Var(m.k, domain=NonNegativeReals)  # energy consumption per building kwh
    m.eg = Var(m.k, domain=NonNegativeReals)  # energy generation per building kwh
    m.eb = Var(m.k, domain=NonNegativeReals)  # energy burden per building
    m.eb_p_plus = Var(m.k, domain=NonNegativeReals)  # burden gap
    m.eb_p_minus = Var(m.k, domain=NonNegativeReals)  # burden over_target

    m.ci = Var(domain=NonNegativeReals)  # annual investment costs
    m.bp_function = Var(domain=NonNegativeReals)  # burden penalty
    m.budget_limit = Param(initialize=budget_limit)
    m.eb_weight = Param(initialize=eb_weight, mutable=True)  # always initialized as 1

    def const_7(m, k):
        return m.c_wth[k] == m.d_wth[k] * m.C_wth[k] * (m.R / (1 - (1 + m.R) ** -m.Lt_wth))

    m.const_7 = Constraint(m.k_w, rule=const_7)

    def const_8(m, k):
        return m.g_rts[k] == m.d_rts[k] * m.rts_prod[k]

    m.const_8 = Constraint(m.k_rts, rule=const_8)

    def const_8_2(m, k):
        return m.g_rts[k] == 0

    m.const_8_2 = Constraint(m.k - m.k_rts, rule=const_8_2)

    def const_9(m, k):
        t = m.kcs_t[k]
        return m.g_cs[k] == m.d_cs[t] * m.cs_prod[k] / sum(m.n_bdg[kcs] for kcs in m.Tk_cs[t])

    m.const_9 = Constraint(m.k_cs, rule=const_9)

    def const_9_2(m, k):
        return m.g_cs[k] == 0

    m.const_9_2 = Constraint(m.k - m.k_cs, rule=const_9_2)

    def const_10(m, k):
        t = m.kcw_t[k]
        return m.g_cw[k] == m.d_cw[t] * m.wnd_prod[k] / sum(m.n_bdg[kcw] for kcw in m.Tk_cw[t])

    m.const_10 = Constraint(m.k_cw, rule=const_10)

    def const_10_2(m, k):
        return m.g_cw[k] == 0

    m.const_10_2 = Constraint(m.k - m.k_cw, rule=const_10_2)

    def const_11(m, k):
        return m.c_rts[k] == m.d_rts[k] * m.C_rts * (m.R / (1 - (1 + m.R) ** -m.Lt_rts))

    m.const_11 = Constraint(m.k_rts, rule=const_11)

    def const_12(m, t):
        return m.c_cs[t] == m.d_cs[t] * m.C_cs * (m.R / (1 - (1 + m.R) ** -m.Lt_cs))

    m.const_12 = Constraint(m.T, rule=const_12)

    def const_13(m, t):
        return m.c_cw[t] == m.d_cw[t] * m.C_cw * (m.R / (1 - (1 + m.R) ** -m.Lt_cw))

    m.const_13 = Constraint(m.T, rule=const_13)

    def const_14(m, k):
        return m.eld[k] == m.C_el[k] / m.P_el[k] - m.d_wth[k] * m.WS[k] * m.C_el[k] / m.P_el[k]

    m.const_14 = Constraint(m.k_w_el, rule=const_14)

    def const_15(m, k):
        return m.eld[k] == m.C_el[k] / m.P_el[k]

    m.const_15 = Constraint(m.k - m.k_w_el, rule=const_15)

    def const_16(m, k):
        return m.ec[k] == m.eld[k] * m.P_el[k] + m.C_gs[k] + m.C_of[k]

    m.const_16 = Constraint(m.k - m.k_w_gs - m.k_w_of, rule=const_16)

    def const_17(m, k):
        return m.ec[k] == m.eld[k] * m.P_el[k] + m.C_gs[k] - (m.C_gs[k] * m.d_wth[k] * m.WS[k]) + m.C_of[k]

    m.const_17 = Constraint(m.k_w_gs, rule=const_17)

    def const_18(m, k):
        return m.ec[k] == m.eld[k] * m.P_el[k] + m.C_gs[k] + m.C_of[k] - (m.C_of[k] * m.d_wth[k] * m.WS[k])

    m.const_18 = Constraint(m.k_w_of, rule=const_18)

    def const_19(m, k):
        return m.eg[k] == m.g_rts[k] + m.g_cs[k] + m.g_cw[k]

    m.const_19 = Constraint(m.k, rule=const_19)

    def const_20(m, k):
        return m.eb[k] == (m.ec[k] - m.eg[k] * m.P_el[k]) / m.income[k]

    m.const_20 = Constraint(m.k, rule=const_20)

    def const_21(m, k):
        return m.eb[k] - eb_target == m.eb_p_plus[k] - m.eb_p_minus[k]

    m.const_21 = Constraint(m.k, rule=const_21)

    def const_22(m, k):
        pass  # Defined in the variable construction

    def const_23(m, k):
        return m.d_wth[k] <= 1

    m.const_23 = Constraint(m.k_w, rule=const_23)

    def const_27(m, k):
        return m.eld[k] >= m.eg[k]

    m.const_27 = Constraint(m.k, rule=const_27)

    def const_28(m, k):
        return m.d_rts[k] * m.n_bdg[k] <= m.rts_max_kw[k]

    m.const_28 = Constraint(m.k_rts, rule=const_28)

    def const_29(m, t):
        return m.d_cw[t] <= sum(m.cw_max_kw[k] for k in m.Tk_cw[t])

    m.const_29 = Constraint(m.T, rule=const_29)

    def objective_first_row(m):
        return m.ci == sum(m.c_cs[t] + m.c_cw[t] for t in m.T) + sum(m.c_rts[k] * m.n_bdg[k] for k in m.k_rts) \
               + sum(m.c_wth[k] * m.n_bdg[k] for k in m.k_w)

    m.objective_first_row = Constraint(rule=objective_first_row)

    def objective_second_row(m):
        return m.bp_function == sum(100 * m.eb_p_plus[k] * m.n_bdg[k] for k in m.k)

    m.objective_second_row = Constraint(rule=objective_second_row)

    def budget_constraint(m):
        return (m.ci - m.eb_weight * m.budget_limit) / 1e6 <= 0

    m.budget_limit_constraint = Constraint(rule=budget_constraint)

    # solving to parameterize the function:

    # 1 - minimize equity
    m.ObjectiveFunction = Objective(rule=m.bp_function)
    opt = SolverFactory(solver)
    results = opt.solve(m)

    # 2 - minimize budget with constrained equity
    equity = m.bp_function.value
    def equity_constraint(m):
        return m.bp_function <= equity
    m.equity_constraint = Constraint(rule=equity_constraint)
    m.del_component(m.ObjectiveFunction)
    m.ObjectiveFunction = Objective(rule=m.ci)
    opt = SolverFactory(solver)
    results = opt.solve(m, tee=True)

    res_df = pd.DataFrame(index=df.index)
    for v in [m.d_wth, m.c_wth,  # weatherization variables
              m.d_rts, m.c_rts,  # rooftop_variables
              m.g_rts, m.g_cs, m.g_cw,  # generation variables
              m.eg, m.ec, m.eld, m.nel,  # energy_cost_variables
              m.eb, m.eb_p_plus, m.eb_p_minus,  # energy burden variables
              ]:
        res_df = res_df.join(pd.Series(v.get_values(), name=v.getname()))

    res_df['C_wth'] = total_cost_cost(res_df['c_wth'], inv_rate, m.Lt_wth.value)
    res_df['C_rts'] = total_cost_cost(res_df['c_rts'], inv_rate, m.Lt_rts.value)

    df_tract = pd.DataFrame(index=df.fips.unique())
    df_tract = df_tract.sort_index()
    for vt in [m.d_cs, m.c_cs,
               m.d_cw, m.c_cw]:
        df_tract = df_tract.join(pd.Series(vt.get_values(), name=vt.getname()))

    df_tract['C_cs'] = total_cost_cost(df_tract['c_cs'], inv_rate, m.Lt_cs.value)
    df_tract['C_cw'] = total_cost_cost(df_tract['c_cw'], inv_rate, m.Lt_cw.value)

    return res_df, df_tract
