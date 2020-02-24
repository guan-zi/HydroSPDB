import unittest

import definitions
from data import GagesConfig, GagesSource, DataModel
from data.data_input import save_datamodel, load_datamodel
from data.gages_input_dataset import GagesDamDataModel
from data.nid_input import NidModel
from explore.stat import statError
from hydroDL.master.master import master_train, master_test
import numpy as np
import os
import pandas as pd
from utils.dataset_format import subset_of_dict
from visual import plot_ts_obs_pred
from visual.plot_model import plot_boxes_inds, plot_ind_map


class MyTestCase(unittest.TestCase):
    """historical data assimilation"""

    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR
        # self.config_file = os.path.join(config_dir, "dam/config_dam_exp1.ini")
        # self.subdir = r"dam/exp1"
        self.config_file = os.path.join(config_dir, "dam/config_dam_exp2.ini")
        self.subdir = r"dam/exp2"
        self.config_data = GagesConfig.set_subdir(self.config_file, self.subdir)
        # self.nid_file = 'PA_U.xlsx'
        self.nid_file = 'OH_U.xlsx'

    def test_data_temp_dam(self):
        config_data_1 = self.config_data
        source_data_1 = GagesSource(config_data_1, config_data_1.model_dict["data"]["tRangeTrain"])
        df1 = DataModel(source_data_1)
        save_datamodel(df1, data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')

    def test_dam_train(self):
        df = load_datamodel(self.config_data.data_path["Temp"], data_source_file_name='data_source.txt',
                            stat_file_name='Statistics.json', flow_file_name='flow.npy',
                            forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                            f_dict_file_name='dictFactorize.json',
                            var_dict_file_name='dictAttribute.json',
                            t_s_dict_file_name='dictTimeSpace.json')
        nid_input = NidModel()
        # nid_input = NidModel(self.nid_file)
        data_input = GagesDamDataModel(df, nid_input)
        master_train(data_input.gages_input)

    def test_data_temp_test_dam(self):
        config_data_test = self.config_data
        source_data_test = GagesSource(config_data_test, config_data_test.model_dict["data"]["tRangeTest"])
        df_test = DataModel(source_data_test)
        save_datamodel(df_test, data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')

    def test_dam_test(self):
        df_test = load_datamodel(self.config_data.data_path["Temp"], data_source_file_name='test_data_source.txt',
                                 stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                 forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                 f_dict_file_name='test_dictFactorize.json',
                                 var_dict_file_name='test_dictAttribute.json',
                                 t_s_dict_file_name='test_dictTimeSpace.json')
        nid_input = NidModel()
        # nid_input = NidModel(self.nid_file)
        data_input_test = GagesDamDataModel(df_test, nid_input)
        pred, obs = master_test(data_input_test.gages_input)
        pred = pred.reshape(pred.shape[0], pred.shape[1])
        obs = obs.reshape(obs.shape[0], obs.shape[1])
        inds = statError(obs, pred)
        show_me_num = 5
        t_s_dict = data_input_test.gages_input.t_s_dict
        sites = np.array(t_s_dict["sites_id"])
        t_range = np.array(t_s_dict["t_final_range"])
        ts_fig = plot_ts_obs_pred(obs, pred, sites, t_range, show_me_num)
        ts_fig.savefig(os.path.join(data_input_test.gages_input.data_source.data_config.data_path["Out"], "ts_fig.png"))
        # # plot box，使用seaborn库
        keys = ["Bias", "RMSE", "NSE"]
        inds_test = subset_of_dict(inds, keys)
        box_fig = plot_boxes_inds(inds_test)
        box_fig.savefig(
            os.path.join(data_input_test.gages_input.data_source.data_config.data_path["Out"], "box_fig.png"))
        # plot map
        sites_df = pd.DataFrame({"sites": sites, keys[2]: inds_test[keys[2]]})
        plot_ind_map(data_input_test.gages_input.data_source.all_configs['gage_point_file'], sites_df)


if __name__ == '__main__':
    unittest.main()
