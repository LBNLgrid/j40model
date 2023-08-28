from j40_model.aux_functions import data_corrections, aggregate_per_tract, eb_percentage
from j40_model.interventions import interventions_main
import pandas as pd
from j40_model.nomenclature import col_map_results, col_map_base
import numpy as np


class CommunityCase:

    def __init__(self, df, cost_table, eb_target):

        df = data_corrections(df)
        df['baseline_ec'] = df[['annual_elec_cost_dol_per_year',
                                'annual_gas_cost_dol_per_year',
                                'annual_fuel_cost_dol_per_year']].sum(axis=1)
        df['baseline_eb'] = df['baseline_ec'] / df['annual_income']

        self.community_table = df

        self.cost_table = cost_table

        self.el_ami = ['80-100%']
        self.el_tenure = ['OWNER', 'RENTER']
        self.fips = df.fips.unique()
        self.policies = ['weatherization', 'rooftop_solar',
                         'community_solar', 'community_wind']

        self.eb_target = eb_target
        self.results_per_bdg = pd.DataFrame()
        self.results_per_tract = pd.DataFrame()

    def run_intervention(self, optimization=False, **kwargs):
        df = self.community_table

        df_e = df.loc[df['baseline_eb'] > self.eb_target]

        eligible = {}
        eligible_index = []
        for p in self.policies:
            el_df = df_e.loc[(df_e.ami.isin(self.el_ami))
                             & (df_e.tenure.isin(self.el_tenure))]
            eligible.update({p: el_df})
            eligible_index += list(el_df.index)

        df_e = df_e.loc[np.unique(eligible_index)].copy()

        # eligibility sets of k
        e_w = eligible['weatherization']
        el_sets = {
            'k_rts': eligible['rooftop_solar'].index.to_list(),  # eligible for rooftop solar
            'k_cs': eligible['community_solar'].index.to_list(),  # eligible for community solar
            'k_cw': eligible['community_wind'].index.to_list(),  # eligible for community wind
            'k_w_el': e_w.loc[e_w.heating_fuel.isin(
                ['ELECTRICITY'])].index.to_list(),  # weatherization + electricity
            'k_w_gs': e_w.loc[e_w.heating_fuel.isin(
                ['BOTTLED GAS', 'UTILITY GAS'])].index.to_list(),  # weatherization + gas
            'k_w_of': e_w.loc[e_w.heating_fuel.isin(
                ['WOOD', 'COAL', 'FUEL OIL', 'OTHER'])].index.to_list(),  # weatherization + fuel
        }

        # run intervention
        self.results_per_bdg, self.results_per_tract = interventions_main(
            df_e=df_e, el_sets=el_sets, energy_burden_target=self.eb_target,
            cost_table=self.cost_table, opt=optimization, **kwargs)

    def _eligible_df(self, just_eligible=False):
        if just_eligible:
            df = self.results_per_bdg.join(self.community_table)
        else:
            df = self.community_table.join(self.results_per_bdg).fillna(0)
            df.loc[~df.index.isin(self.results_per_bdg.index), 'ec'] = df.loc[
                ~df.index.isin(self.results_per_bdg.index), 'baseline_ec']
            df.loc[~df.index.isin(self.results_per_bdg.index), 'eb'] = df.loc[
                ~df.index.isin(self.results_per_bdg.index), 'baseline_eb']

        return df

    def get_results_per_building(self, just_eligible=False):
        df = self._eligible_df(just_eligible=just_eligible)
        df = df[col_map_results.keys()]
        df = df.rename(columns=col_map_results)
        df = eb_percentage(df)
        return df

    def get_results_per_tract(self, just_eligible=False):
        df = self._eligible_df(just_eligible=just_eligible)
        # aggregate building results per tract and join
        summed_keys = ['d_wth', 'C_wth', 'c_wth',
                       'd_rts', 'C_rts', 'c_rts', 'g_rts',
                       'g_cs',  'g_cw',
                       'solar_kw_potential', 'wind_kw_potential'
                       ]
        weighted_keys = ['baseline_ec', 'baseline_eb', 'ec', 'eb', 'jobs_per_home']
        t_df = aggregate_per_tract(df, summed_keys, weighted_keys)
        t_df = t_df.join(self.results_per_tract).fillna(0)
        t_df = t_df.rename(columns=col_map_results)
        t_df = eb_percentage(t_df)
        return t_df

    def get_base_per_tract(self):
        df = self.community_table
        summed_keys = []
        weighted_keys = ['baseline_ec', 'baseline_eb']
        t_df = aggregate_per_tract(df, summed_keys, weighted_keys)
        t_df = t_df.rename(columns=col_map_base)
        t_df = eb_percentage(t_df)
        return t_df
