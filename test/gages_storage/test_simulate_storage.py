import unittest

import torch

import definitions
from data import GagesConfig, GagesSource
from data.data_config import add_model_param
from data.data_input import save_datamodel, GagesModel, _basin_norm, save_result
from data.gages_input_dataset import GagesStorageDataModel
from explore.stat import statError
from hydroDL.master.master import train_lstm_storage, test_lstm_storage
import numpy as np
import os
import pandas as pd
from utils import unserialize_numpy
from utils.dataset_format import subset_of_dict
from visual import plot_ts_obs_pred
from visual.plot_model import plot_map
from visual.plot_stat import plot_ecdf, plot_diff_boxes


class MyTestCaseSimulateAndInv(unittest.TestCase):
    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR
        self.config_file_natflow = os.path.join(config_dir, "storage/config1_exp2.ini")
        self.config_file_storage = os.path.join(config_dir, "storage/config2_exp2.ini")
        self.subdir = r"storage/exp2"
        self.config_data_natflow = GagesConfig.set_subdir(self.config_file_natflow, self.subdir)
        self.config_data_storage = GagesConfig.set_subdir(self.config_file_storage, self.subdir)
        # To simulate storage, get info from previous T time-seq natflow (set several months)
        add_model_param(self.config_data_storage, "model", storageLength=100, seqLength=1)
        test_epoch_lst = [100, 200, 220, 250, 280, 290, 295, 300, 305, 310, 320, 400, 500]
        # self.test_epoch = test_epoch_lst[0]
        # self.test_epoch = test_epoch_lst[1]
        # self.test_epoch = test_epoch_lst[2]
        # self.test_epoch = test_epoch_lst[3]
        # self.test_epoch = test_epoch_lst[4]
        # self.test_epoch = test_epoch_lst[5]
        # self.test_epoch = test_epoch_lst[6]
        self.test_epoch = test_epoch_lst[7]
        # self.test_epoch = test_epoch_lst[8]
        # self.test_epoch = test_epoch_lst[9]
        # self.test_epoch = test_epoch_lst[10]
        # self.test_epoch = test_epoch_lst[11]
        # self.test_epoch = test_epoch_lst[12]

    def test_siminv_data_temp(self):
        quick_data_dir = os.path.join(self.config_data_natflow.data_path["DB"], "quickdata")
        # data_dir = os.path.join(quick_data_dir, "conus-all_85-05_nan-0.1_00-1.0")
        data_dir = os.path.join(quick_data_dir, "conus-all_90-10_nan-0.0_00-1.0")
        data_model_8595 = GagesModel.load_datamodel(data_dir,
                                                    data_source_file_name='data_source.txt',
                                                    stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                    forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                    f_dict_file_name='dictFactorize.json',
                                                    var_dict_file_name='dictAttribute.json',
                                                    t_s_dict_file_name='dictTimeSpace.json')
        data_model_9505 = GagesModel.load_datamodel(data_dir,
                                                    data_source_file_name='test_data_source.txt',
                                                    stat_file_name='test_Statistics.json',
                                                    flow_file_name='test_flow.npy',
                                                    forcing_file_name='test_forcing.npy',
                                                    attr_file_name='test_attr.npy',
                                                    f_dict_file_name='test_dictFactorize.json',
                                                    var_dict_file_name='test_dictAttribute.json',
                                                    t_s_dict_file_name='test_dictTimeSpace.json')

        conus_sites_id = data_model_8595.t_s_dict["sites_id"]
        nomajordam_source_data = GagesSource.choose_some_basins(self.config_data_natflow,
                                                                self.config_data_natflow.model_dict["data"][
                                                                    "tRangeTrain"],
                                                                screen_basin_area_huc4=False, major_dam_num=0)
        nomajordam_sites_id = nomajordam_source_data.all_configs['flow_screen_gage_id']
        nomajordam_in_conus = np.intersect1d(conus_sites_id, nomajordam_sites_id)
        majordam_source_data = GagesSource.choose_some_basins(self.config_data_natflow,
                                                              self.config_data_natflow.model_dict["data"][
                                                                  "tRangeTrain"],
                                                              screen_basin_area_huc4=False, major_dam_num=[1, 2000])
        majordam_sites_id = majordam_source_data.all_configs['flow_screen_gage_id']
        majordam_in_conus = np.intersect1d(conus_sites_id, majordam_sites_id)

        t_range_train_natflow = self.config_data_natflow.model_dict["data"]["tRangeTrain"]
        t_range_test_natflow = self.config_data_natflow.model_dict["data"]["tRangeTest"]
        gages_model_train_natflow = GagesModel.update_data_model(self.config_data_natflow, data_model_8595,
                                                                 sites_id_update=nomajordam_in_conus,
                                                                 t_range_update=t_range_train_natflow,
                                                                 data_attr_update=True, screen_basin_area_huc4=False)
        gages_model_test_natflow = GagesModel.update_data_model(self.config_data_natflow, data_model_9505,
                                                                sites_id_update=nomajordam_in_conus,
                                                                t_range_update=t_range_test_natflow,
                                                                data_attr_update=True,
                                                                train_stat_dict=gages_model_train_natflow.stat_dict,
                                                                screen_basin_area_huc4=False)
        t_range_train_storage = self.config_data_storage.model_dict["data"]["tRangeTrain"]
        t_range_test_storage = self.config_data_storage.model_dict["data"]["tRangeTest"]
        gages_model_train_storage = GagesModel.update_data_model(self.config_data_storage, data_model_8595,
                                                                 sites_id_update=majordam_in_conus,
                                                                 t_range_update=t_range_train_storage,
                                                                 data_attr_update=True, screen_basin_area_huc4=False)
        gages_model_test_storage = GagesModel.update_data_model(self.config_data_storage, data_model_9505,
                                                                sites_id_update=majordam_in_conus,
                                                                t_range_update=t_range_test_storage,
                                                                data_attr_update=True,
                                                                train_stat_dict=gages_model_train_storage.stat_dict,
                                                                screen_basin_area_huc4=False)

        save_datamodel(gages_model_train_natflow, "1", data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(gages_model_test_natflow, "1", data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        save_datamodel(gages_model_train_storage, "2", data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(gages_model_test_storage, "2", data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        print("read and save data model")

    def test_storage_train(self):
        with torch.cuda.device(0):
            df1 = GagesModel.load_datamodel(self.config_data_natflow.data_path["Temp"], "1",
                                            data_source_file_name='data_source.txt',
                                            stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                            forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                            f_dict_file_name='dictFactorize.json',
                                            var_dict_file_name='dictAttribute.json',
                                            t_s_dict_file_name='dictTimeSpace.json')
            df1.update_model_param('train', nEpoch=300)
            df2 = GagesModel.load_datamodel(self.config_data_storage.data_path["Temp"], "2",
                                            data_source_file_name='data_source.txt',
                                            stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                            forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                            f_dict_file_name='dictFactorize.json',
                                            var_dict_file_name='dictAttribute.json',
                                            t_s_dict_file_name='dictTimeSpace.json')
            data_model = GagesStorageDataModel(df1, df2)
            pre_trained_model_epoch = 170
            train_lstm_storage(data_model, pre_trained_model_epoch=pre_trained_model_epoch)
            # train_lstm_storage(data_model)

    def test_storage_test(self):
        with torch.cuda.device(0):
            df1 = GagesModel.load_datamodel(self.config_data_natflow.data_path["Temp"], "1",
                                            data_source_file_name='test_data_source.txt',
                                            stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                            forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                            f_dict_file_name='test_dictFactorize.json',
                                            var_dict_file_name='test_dictAttribute.json',
                                            t_s_dict_file_name='test_dictTimeSpace.json')
            df1.update_model_param('train', nEpoch=300)
            df2 = GagesModel.load_datamodel(self.config_data_storage.data_path["Temp"], "2",
                                            data_source_file_name='test_data_source.txt',
                                            stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                            forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                            f_dict_file_name='test_dictFactorize.json',
                                            var_dict_file_name='test_dictAttribute.json',
                                            t_s_dict_file_name='test_dictTimeSpace.json')
            data_model = GagesStorageDataModel(df1, df2)
            test_epoch = self.test_epoch
            pred, obs = test_lstm_storage(data_model, epoch=test_epoch)
            basin_area = df2.data_source.read_attr(df2.t_s_dict["sites_id"], ['DRAIN_SQKM'], is_return_dict=False)
            mean_prep = df2.data_source.read_attr(df2.t_s_dict["sites_id"], ['PPTAVG_BASIN'], is_return_dict=False)
            mean_prep = mean_prep / 365 * 10
            pred = _basin_norm(pred, basin_area, mean_prep, to_norm=False)
            obs = _basin_norm(obs, basin_area, mean_prep, to_norm=False)
            save_result(df2.data_source.data_config.data_path['Temp'], test_epoch, pred, obs)

    def test_siminv_plot(self):
        data_model = GagesModel.load_datamodel(self.config_data_lstm.data_path["Temp"], "3",
                                               data_source_file_name='test_data_source.txt',
                                               stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                               forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                               f_dict_file_name='test_dictFactorize.json',
                                               var_dict_file_name='test_dictAttribute.json',
                                               t_s_dict_file_name='test_dictTimeSpace.json')
        test_epoch = self.test_epoch
        flow_pred_file = os.path.join(data_model.data_source.data_config.data_path['Temp'],
                                      'epoch' + str(test_epoch) + 'flow_pred.npy')
        flow_obs_file = os.path.join(data_model.data_source.data_config.data_path['Temp'],
                                     'epoch' + str(test_epoch) + 'flow_obs.npy')
        pred = unserialize_numpy(flow_pred_file)
        obs = unserialize_numpy(flow_obs_file)
        pred = pred.reshape(pred.shape[0], pred.shape[1])
        obs = obs.reshape(obs.shape[0], obs.shape[1])

        inds = statError(obs, pred)
        inds['STAID'] = data_model.t_s_dict["sites_id"]
        inds_df = pd.DataFrame(inds)
        inds_df.to_csv(os.path.join(self.config_data_lstm.data_path["Out"], 'data_df.csv'))
        # plot box，使用seaborn库
        keys = ["Bias", "RMSE", "NSE"]
        inds_test = subset_of_dict(inds, keys)
        box_fig = plot_diff_boxes(inds_test)
        box_fig.savefig(os.path.join(self.config_data_lstm.data_path["Out"], "box_fig.png"))
        # plot ts
        show_me_num = 5
        t_s_dict = data_model.t_s_dict
        sites = np.array(t_s_dict["sites_id"])
        t_range = np.array(t_s_dict["t_final_range"])
        time_seq_length = self.config_data_storage.model_dict["model"]["seqLength"]
        time_start = np.datetime64(t_range[0]) + np.timedelta64(time_seq_length - 1, 'D')
        t_range[0] = np.datetime_as_string(time_start, unit='D')
        ts_fig = plot_ts_obs_pred(obs, pred, sites, t_range, show_me_num)
        ts_fig.savefig(os.path.join(self.config_data_lstm.data_path["Out"], "ts_fig.png"))

        # plot nse ecdf
        sites_df_nse = pd.DataFrame({"sites": sites, keys[2]: inds_test[keys[2]]})
        plot_ecdf(sites_df_nse, keys[2])
        # plot map
        gauge_dict = data_model.data_source.gage_dict
        plot_map(gauge_dict, sites_df_nse, id_col="STAID", lon_col="LNG_GAGE", lat_col="LAT_GAGE")


if __name__ == '__main__':
    unittest.main()
