import os
import unittest

import torch

import definitions
from data import CamelsConfig
from data.data_input import save_datamodel, CamelsModel, _basin_norm
from data.camels_input_dataset import CamelsModels
from hydroDL.master.master import master_train_batch1st_lstm, master_test_batch1st_lstm
from visual.plot_model import plot_we_need


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR
        # self.config_file = os.path.join(config_dir, "camelshuf/config_exp1.ini")
        # self.subdir = r"camelshuf/exp1"
        # self.config_file = os.path.join(config_dir, "camelshuf/config_exp2.ini")
        # self.subdir = r"camelshuf/exp2"
        # self.config_file = os.path.join(config_dir, "camelshuf/config_exp3.ini")
        # self.subdir = r"camelshuf/exp3"
        # self.config_file = os.path.join(config_dir, "camelshuf/config_exp4.ini")
        # self.subdir = r"camelshuf/exp4"
        # self.config_file = os.path.join(config_dir, "camelshuf/config_exp5.ini")
        # self.subdir = r"camelshuf/exp5"
        self.config_file = os.path.join(config_dir, "camelshuf/config_exp6.ini")
        self.subdir = r"camelshuf/exp6"
        self.config_data = CamelsConfig.set_subdir(self.config_file, self.subdir)

    def test_shuffle_datamodel(self):
        # 准备训练数据
        camels_model = CamelsModels(self.config_data)
        save_datamodel(camels_model.data_model_train, data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(camels_model.data_model_test, data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        print("read and save data model")

    def test_train_shuffle_camels(self):
        data_model = CamelsModel.load_datamodel(self.config_data.data_path["Temp"],
                                                data_source_file_name='data_source.txt',
                                                stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                f_dict_file_name='dictFactorize.json',
                                                var_dict_file_name='dictAttribute.json',
                                                t_s_dict_file_name='dictTimeSpace.json')
        with torch.cuda.device(1):
            master_train_batch1st_lstm(data_model)

    def test_test_camels(self):
        data_model = CamelsModel.load_datamodel(self.config_data.data_path["Temp"],
                                                data_source_file_name='test_data_source.txt',
                                                stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                                forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                                f_dict_file_name='test_dictFactorize.json',
                                                var_dict_file_name='test_dictAttribute.json',
                                                t_s_dict_file_name='test_dictTimeSpace.json')
        with torch.cuda.device(1):
            # pred, obs = master_test(data_model)
            pred, obs = master_test_batch1st_lstm(data_model, load_epoch=260)
            basin_area = data_model.data_source.read_attr(data_model.t_s_dict["sites_id"], ['area_gages2'],
                                                          is_return_dict=False)
            mean_prep = data_model.data_source.read_attr(data_model.t_s_dict["sites_id"], ['p_mean'],
                                                         is_return_dict=False)
            pred = _basin_norm(pred, basin_area, mean_prep, to_norm=False)
            obs = _basin_norm(obs, basin_area, mean_prep, to_norm=False)
            plot_we_need(data_model, obs, pred)


if __name__ == '__main__':
    unittest.main()
