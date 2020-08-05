import os
import unittest

import torch

from data import *
from data.data_input import save_datamodel, GagesModel, _basin_norm, save_result, load_result
from data.gages_input_dataset import GagesModels, load_dataconfig_case_exp
from explore.stat import statError, ecdf
from hydroDL.master import *
import definitions
from hydroDL.master.master import master_train_warmup
from utils import hydro_time
from visual.plot_model import plot_we_need
from visual.plot_stat import plot_ecdfs


class MyTestCaseGages(unittest.TestCase):
    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR

        # self.config_file = os.path.join(config_dir, "basic/config_exp38.ini")
        # self.subdir = r"basic/exp38"
        # self.random_seed = 1234
        # self.config_file = os.path.join(config_dir, "warmup/config_exp1.ini")
        # self.subdir = r"warmup/exp1"
        # self.random_seed = 1234
        self.config_file = os.path.join(config_dir, "warmup/config_exp2.ini")
        self.subdir = r"warmup/exp2"
        self.random_seed = 1234

        self.config_data = GagesConfig.set_subdir(self.config_file, self.subdir)
        test_epoch_lst = [100, 140, 200, 220, 250, 280, 290, 300, 310, 320, 350]
        # self.test_epoch = test_epoch_lst[0]
        self.test_epoch = test_epoch_lst[1]
        # self.test_epoch = test_epoch_lst[2]
        # self.test_epoch = test_epoch_lst[3]
        # self.test_epoch = test_epoch_lst[4]
        # self.test_epoch = test_epoch_lst[5]
        # self.test_epoch = test_epoch_lst[6]
        # self.test_epoch = test_epoch_lst[7]
        # self.test_epoch = test_epoch_lst[8]
        # self.test_epoch = test_epoch_lst[9]
        # self.test_epoch = test_epoch_lst[10]

    def test_gages_data_model(self):
        gages_model = GagesModels(self.config_data, screen_basin_area_huc4=False)
        save_datamodel(gages_model.data_model_train, data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(gages_model.data_model_test, data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        print("read and save data model")

    def test_train_gages(self):
        data_model = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                               data_source_file_name='data_source.txt',
                                               stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                               forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                               f_dict_file_name='dictFactorize.json',
                                               var_dict_file_name='dictAttribute.json',
                                               t_s_dict_file_name='dictTimeSpace.json')
        with torch.cuda.device(0):
            # pre_trained_model_epoch = 220
            master_train_warmup(data_model, warmup_len=120, random_seed=self.random_seed)
            # master_train(data_model, random_seed=self.random_seed)

    def test_test_gages(self):
        data_model_origin = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                                      data_source_file_name='test_data_source.txt',
                                                      stat_file_name='test_Statistics.json',
                                                      flow_file_name='test_flow.npy',
                                                      forcing_file_name='test_forcing.npy',
                                                      attr_file_name='test_attr.npy',
                                                      f_dict_file_name='test_dictFactorize.json',
                                                      var_dict_file_name='test_dictAttribute.json',
                                                      t_s_dict_file_name='test_dictTimeSpace.json')
        warmup_len = 120
        t_range_all = data_model_origin.t_s_dict["t_final_range"]
        t_range_lst = hydro_time.t_range_days(t_range_all)
        t_range_warmup = hydro_time.t_days_lst2range(t_range_lst[:warmup_len])
        t_range_test = hydro_time.t_days_lst2range(t_range_lst[warmup_len:])
        data_model_warmup, data_model = GagesModel.data_models_of_train_test(data_model_origin, t_range_warmup,
                                                                             t_range_test)
        data_model.stat_dict = data_model_origin.stat_dict
        with torch.cuda.device(0):
            pred, obs = master_test(data_model, epoch=self.test_epoch)
            basin_area = data_model.data_source.read_attr(data_model.t_s_dict["sites_id"], ['DRAIN_SQKM'],
                                                          is_return_dict=False)
            mean_prep = data_model.data_source.read_attr(data_model.t_s_dict["sites_id"], ['PPTAVG_BASIN'],
                                                         is_return_dict=False)
            mean_prep = mean_prep / 365 * 10
            pred = _basin_norm(pred, basin_area, mean_prep, to_norm=False)
            obs = _basin_norm(obs, basin_area, mean_prep, to_norm=False)
            save_result(data_model.data_source.data_config.data_path['Temp'], self.test_epoch, pred, obs)
            plot_we_need(data_model, obs, pred, id_col="STAID", lon_col="LNG_GAGE", lat_col="LAT_GAGE")

    def test_plot_ecdf_together(self):
        xs = []
        ys = []
        cases_exps = ["basic_exp38", "warmup_exp1"]
        cases_exps_legends = ["without_warmup", "with_warmup"]
        for case_exp in cases_exps:
            config_data_i = load_dataconfig_case_exp(case_exp)
            pred_i, obs_i = load_result(config_data_i.data_path['Temp'], self.test_epoch)
            pred_i = pred_i.reshape(pred_i.shape[0], pred_i.shape[1])
            obs_i = obs_i.reshape(obs_i.shape[0], obs_i.shape[1])
            inds_i = statError(obs_i, pred_i)
            x, y = ecdf(inds_i["NSE"])
            xs.append(x)
            ys.append(y)
        plot_ecdfs(xs, ys, cases_exps_legends)


if __name__ == '__main__':
    unittest.main()