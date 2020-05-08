import unittest

import torch

import definitions
from data import GagesConfig, GagesSource
from data.data_input import GagesModel, _basin_norm, save_datamodel, save_result, load_result
from data.gages_input_dataset import GagesDamDataModel, choose_which_purpose, load_dataconfig_case_exp
from data.nid_input import NidModel
from explore.gages_stat import split_results_to_regions
from explore.stat import statError, ecdf
from hydroDL.master.master import master_train, master_test
import numpy as np
import os
import pandas as pd

from utils import unserialize_json
from utils.dataset_format import subset_of_dict
from visual import plot_ts_obs_pred
from visual.plot_model import plot_we_need, plot_map
from visual.plot_stat import plot_ecdf, plot_diff_boxes, plot_ecdfs


class MyTestCase(unittest.TestCase):
    """data pre-process and post-process"""

    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR
        self.config_file = os.path.join(config_dir, "dam/config_exp16.ini")
        self.subdir = r"dam/exp16"
        self.config_data = GagesConfig.set_subdir(self.config_file, self.subdir)
        # self.nid_file = 'PA_U.xlsx'
        # self.nid_file = 'OH_U.xlsx'
        self.nid_file = 'NID2018_U.xlsx'
        self.test_epoch = 300

    def test_gages_data_model(self):
        config_data = self.config_data
        dam_num = [1, 2000]  # max dam num is 1740
        source_data = GagesSource.choose_some_basins(config_data, config_data.model_dict["data"]["tRangeTrain"],
                                                     screen_basin_area_huc4=False, dam_num=dam_num)
        sites_id = source_data.all_configs['flow_screen_gage_id']
        quick_data_dir = os.path.join(self.config_data.data_path["DB"], "quickdata")
        data_dir = os.path.join(quick_data_dir, "conus-all_85-05_nan-0.1_00-1.0")
        data_model_train = GagesModel.load_datamodel(data_dir,
                                                     data_source_file_name='data_source.txt',
                                                     stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                     forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                     f_dict_file_name='dictFactorize.json',
                                                     var_dict_file_name='dictAttribute.json',
                                                     t_s_dict_file_name='dictTimeSpace.json')
        data_model_test = GagesModel.load_datamodel(data_dir,
                                                    data_source_file_name='test_data_source.txt',
                                                    stat_file_name='test_Statistics.json',
                                                    flow_file_name='test_flow.npy',
                                                    forcing_file_name='test_forcing.npy',
                                                    attr_file_name='test_attr.npy',
                                                    f_dict_file_name='test_dictFactorize.json',
                                                    var_dict_file_name='test_dictAttribute.json',
                                                    t_s_dict_file_name='test_dictTimeSpace.json')
        gages_model_train = GagesModel.update_data_model(self.config_data, data_model_train, sites_id_update=sites_id,
                                                         screen_basin_area_huc4=False)
        gages_model_test = GagesModel.update_data_model(self.config_data, data_model_test, sites_id_update=sites_id,
                                                        train_stat_dict=gages_model_train.stat_dict,
                                                        screen_basin_area_huc4=False)
        save_datamodel(gages_model_train, data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(gages_model_test, data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        print("read and save data model")

    def test_dam_train(self):
        with torch.cuda.device(0):
            gages_model_train = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                                          data_source_file_name='data_source.txt',
                                                          stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                          forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                          f_dict_file_name='dictFactorize.json',
                                                          var_dict_file_name='dictAttribute.json',
                                                          t_s_dict_file_name='dictTimeSpace.json')
            master_train(gages_model_train)
            # pre_trained_model_epoch = 100
            # master_train(gages_model_train, pre_trained_model_epoch=pre_trained_model_epoch)

    def test_dam_test(self):
        with torch.cuda.device(1):
            data_model_test = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                                        data_source_file_name='test_data_source.txt',
                                                        stat_file_name='test_Statistics.json',
                                                        flow_file_name='test_flow.npy',
                                                        forcing_file_name='test_forcing.npy',
                                                        attr_file_name='test_attr.npy',
                                                        f_dict_file_name='test_dictFactorize.json',
                                                        var_dict_file_name='test_dictAttribute.json',
                                                        t_s_dict_file_name='test_dictTimeSpace.json')
            gages_input = GagesModel.update_data_model(self.config_data, data_model_test)
            pred, obs = master_test(gages_input, epoch=self.test_epoch)
            basin_area = gages_input.data_source.read_attr(gages_input.t_s_dict["sites_id"], ['DRAIN_SQKM'],
                                                           is_return_dict=False)
            mean_prep = gages_input.data_source.read_attr(gages_input.t_s_dict["sites_id"], ['PPTAVG_BASIN'],
                                                          is_return_dict=False)
            mean_prep = mean_prep / 365 * 10
            pred = _basin_norm(pred, basin_area, mean_prep, to_norm=False)
            obs = _basin_norm(obs, basin_area, mean_prep, to_norm=False)
            save_result(gages_input.data_source.data_config.data_path['Temp'], self.test_epoch, pred, obs)
            plot_we_need(gages_input, obs, pred, id_col="STAID", lon_col="LNG_GAGE", lat_col="LAT_GAGE")

    def test_purposes_seperate(self):
        quick_data_dir = os.path.join(self.config_data.data_path["DB"], "quickdata")
        data_dir = os.path.join(quick_data_dir, "allnonref-dam_95-05_nan-0.1_00-1.0")
        data_model_test = GagesModel.load_datamodel(data_dir,
                                                    data_source_file_name='test_data_source.txt',
                                                    stat_file_name='test_Statistics.json',
                                                    flow_file_name='test_flow.npy',
                                                    forcing_file_name='test_forcing.npy',
                                                    attr_file_name='test_attr.npy',
                                                    f_dict_file_name='test_dictFactorize.json',
                                                    var_dict_file_name='test_dictAttribute.json',
                                                    t_s_dict_file_name='test_dictTimeSpace.json')
        data_model = GagesModel.update_data_model(self.config_data, data_model_test)
        nid_dir = os.path.join("/".join(self.config_data.data_path["DB"].split("/")[:-1]), "nid", "quickdata")
        gage_main_dam_purpose = unserialize_json(os.path.join(nid_dir, "dam_main_purpose_dict.json"))
        gage_main_dam_purpose_lst = list(gage_main_dam_purpose.values())
        gage_main_dam_purpose_unique = np.unique(gage_main_dam_purpose_lst)
        purpose_regions = {}
        for i in range(gage_main_dam_purpose_unique.size):
            sites_id = []
            for key, value in gage_main_dam_purpose.items():
                if value == gage_main_dam_purpose_unique[i]:
                    sites_id.append(key)
            assert (all(x < y for x, y in zip(sites_id, sites_id[1:])))
            purpose_regions[gage_main_dam_purpose_unique[i]] = sites_id
        id_regions_idx = []
        id_regions_sites_ids = []
        df_id_region = np.array(data_model.t_s_dict["sites_id"])
        for key, value in purpose_regions.items():
            gages_id = value
            c, ind1, ind2 = np.intersect1d(df_id_region, gages_id, return_indices=True)
            assert (all(x < y for x, y in zip(ind1, ind1[1:])))
            assert (all(x < y for x, y in zip(c, c[1:])))
            id_regions_idx.append(ind1)
            id_regions_sites_ids.append(c)
        pred_all, obs_all = load_result(self.config_data.data_path["Temp"], self.test_epoch)
        pred_all = pred_all.reshape(pred_all.shape[0], pred_all.shape[1])
        obs_all = obs_all.reshape(obs_all.shape[0], obs_all.shape[1])
        for i in range(9, len(gage_main_dam_purpose_unique)):
            pred = pred_all[id_regions_idx[i], :]
            obs = obs_all[id_regions_idx[i], :]
            inds = statError(obs, pred)
            inds['STAID'] = id_regions_sites_ids[i]
            inds_df = pd.DataFrame(inds)
            inds_df.to_csv(os.path.join(self.config_data.data_path["Out"],
                                        gage_main_dam_purpose_unique[i] + "epoch" + str(
                                            self.test_epoch) + 'data_df.csv'))
            # plot box，使用seaborn库
            keys = ["Bias", "RMSE", "NSE"]
            inds_test = subset_of_dict(inds, keys)
            box_fig = plot_diff_boxes(inds_test)
            box_fig.savefig(os.path.join(self.config_data.data_path["Out"],
                                         gage_main_dam_purpose_unique[i] + "epoch" + str(
                                             self.test_epoch) + "box_fig.png"))
            # plot ts
            sites = np.array(df_id_region[id_regions_idx[i]])
            t_range = np.array(data_model.t_s_dict["t_final_range"])
            show_me_num = 1
            ts_fig = plot_ts_obs_pred(obs, pred, sites, t_range, show_me_num)
            ts_fig.savefig(os.path.join(self.config_data.data_path["Out"],
                                        gage_main_dam_purpose_unique[i] + "epoch" + str(
                                            self.test_epoch) + "ts_fig.png"))
            # plot nse ecdf
            sites_df_nse = pd.DataFrame({"sites": sites, keys[2]: inds_test[keys[2]]})
            plot_ecdf(sites_df_nse, keys[2], os.path.join(self.config_data.data_path["Out"],
                                                          gage_main_dam_purpose_unique[i] + "epoch" + str(
                                                              self.test_epoch) + "ecdf_fig.png"))
            # plot map
            gauge_dict = data_model.data_source.gage_dict
            save_map_file = os.path.join(self.config_data.data_path["Out"],
                                         gage_main_dam_purpose_unique[i] + "epoch" + str(
                                             self.test_epoch) + "map_fig.png")
            plot_map(gauge_dict, sites_df_nse, save_file=save_map_file, id_col="STAID", lon_col="LNG_GAGE",
                     lat_col="LAT_GAGE")

    def test_purposes_inds(self):
        quick_data_dir = os.path.join(self.config_data.data_path["DB"], "quickdata")
        data_dir = os.path.join(quick_data_dir, "allnonref-dam_95-05_nan-0.1_00-1.0")
        data_model = GagesModel.load_datamodel(data_dir,
                                               data_source_file_name='test_data_source.txt',
                                               stat_file_name='test_Statistics.json',
                                               flow_file_name='test_flow.npy',
                                               forcing_file_name='test_forcing.npy',
                                               attr_file_name='test_attr.npy',
                                               f_dict_file_name='test_dictFactorize.json',
                                               var_dict_file_name='test_dictAttribute.json',
                                               t_s_dict_file_name='test_dictTimeSpace.json')
        gages_data_model = GagesModel.update_data_model(self.config_data, data_model)
        nid_dir = os.path.join("/".join(self.config_data.data_path["DB"].split("/")[:-1]), "nid", "quickdata")
        gage_main_dam_purpose = unserialize_json(os.path.join(nid_dir, "dam_main_purpose_dict.json"))
        gage_main_dam_purpose_lst = list(gage_main_dam_purpose.values())
        gage_main_dam_purpose_unique = np.unique(gage_main_dam_purpose_lst)
        purpose_regions = {}
        for i in range(gage_main_dam_purpose_unique.size):
            sites_id = []
            for key, value in gage_main_dam_purpose.items():
                if value == gage_main_dam_purpose_unique[i]:
                    sites_id.append(key)
            assert (all(x < y for x, y in zip(sites_id, sites_id[1:])))
            purpose_regions[gage_main_dam_purpose_unique[i]] = sites_id
        id_regions_idx = []
        id_regions_sites_ids = []
        df_id_region = np.array(gages_data_model.t_s_dict["sites_id"])
        for key, value in purpose_regions.items():
            gages_id = value
            c, ind1, ind2 = np.intersect1d(df_id_region, gages_id, return_indices=True)
            assert (all(x < y for x, y in zip(ind1, ind1[1:])))
            assert (all(x < y for x, y in zip(c, c[1:])))
            id_regions_idx.append(ind1)
            id_regions_sites_ids.append(c)
        preds, obss, inds_dfs = split_results_to_regions(gages_data_model, self.test_epoch, id_regions_idx,
                                                         id_regions_sites_ids)
        region_names = list(purpose_regions.keys())
        inds_medians = []
        inds_means = []
        for i in range(len(region_names)):
            inds_medians.append(inds_dfs[i].median(axis=0))
            inds_means.append(inds_dfs[i].mean(axis=0))
        print(inds_medians)
        print(inds_means)

    def test_stor_seperate(self):
        config_dir = definitions.CONFIG_DIR
        config_file = os.path.join(config_dir, "basic/config_exp18.ini")
        subdir = r"basic/exp18"
        config_data = GagesConfig.set_subdir(config_file, subdir)
        data_model = GagesModel.load_datamodel(config_data.data_path["Temp"],
                                               data_source_file_name='test_data_source.txt',
                                               stat_file_name='test_Statistics.json',
                                               flow_file_name='test_flow.npy',
                                               forcing_file_name='test_forcing.npy',
                                               attr_file_name='test_attr.npy',
                                               f_dict_file_name='test_dictFactorize.json',
                                               var_dict_file_name='test_dictAttribute.json',
                                               t_s_dict_file_name='test_dictTimeSpace.json')
        all_sites = data_model.t_s_dict["sites_id"]
        storage_nor_1 = [0, 50]
        storage_nor_2 = [50, 15000]  # max is 14348.6581036888
        source_data_nor1 = GagesSource.choose_some_basins(config_data, config_data.model_dict["data"]["tRangeTrain"],
                                                          STORAGE=storage_nor_1)
        source_data_nor2 = GagesSource.choose_some_basins(config_data, config_data.model_dict["data"]["tRangeTrain"],
                                                          STORAGE=storage_nor_2)
        sites_id_nor1 = source_data_nor1.all_configs['flow_screen_gage_id']
        sites_id_nor2 = source_data_nor2.all_configs['flow_screen_gage_id']
        idx_lst_nor1 = [i for i in range(len(all_sites)) if all_sites[i] in sites_id_nor1]
        idx_lst_nor2 = [i for i in range(len(all_sites)) if all_sites[i] in sites_id_nor2]

        pred, obs = load_result(data_model.data_source.data_config.data_path['Temp'], self.test_epoch)
        pred = pred.reshape(pred.shape[0], pred.shape[1])
        obs = obs.reshape(pred.shape[0], pred.shape[1])
        inds = statError(obs, pred)
        inds_df = pd.DataFrame(inds)

        keys_nse = "NSE"
        xs = []
        ys = []
        cases_exps_legends_together = ["small_stor", "large_stor"]

        x1, y1 = ecdf(inds_df[keys_nse].iloc[idx_lst_nor1])
        xs.append(x1)
        ys.append(y1)

        x2, y2 = ecdf(inds_df[keys_nse].iloc[idx_lst_nor2])
        xs.append(x2)
        ys.append(y2)

        cases_exps = ["dam_exp12", "dam_exp11"]
        cases_exps_legends_separate = ["small_stor", "large_stor"]
        # cases_exps = ["dam_exp4", "dam_exp5", "dam_exp6"]
        # cases_exps = ["dam_exp1", "dam_exp2", "dam_exp3"]
        # cases_exps_legends = ["dam-lstm", "dam-with-natural-flow", "dam-with-kernel"]
        for case_exp in cases_exps:
            config_data_i = load_dataconfig_case_exp(case_exp)
            pred_i, obs_i = load_result(config_data_i.data_path['Temp'], self.test_epoch)
            pred_i = pred_i.reshape(pred_i.shape[0], pred_i.shape[1])
            obs_i = obs_i.reshape(obs_i.shape[0], obs_i.shape[1])
            inds_i = statError(obs_i, pred_i)
            x, y = ecdf(inds_i[keys_nse])
            xs.append(x)
            ys.append(y)

        plot_ecdfs(xs, ys, cases_exps_legends_together + cases_exps_legends_separate,
                   style=["together", "together", "separate", "separate"])


if __name__ == '__main__':
    unittest.main()