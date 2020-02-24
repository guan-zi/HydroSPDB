import unittest

import definitions
from data import GagesConfig, GagesSource, DataModel
from data.data_input import save_datamodel, load_datamodel
from data.gages_input_dataset import GagesExploreDataModel, GagesDamDataModel
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
        # self.config_file = os.path.join(config_dir, "damcls/config_damcls_exp1.ini")  # classify_datamodel
        # self.subdir = r"damcls/exp1"
        # self.config_file = os.path.join(config_dir, "damcls/config_damcls_exp2.ini") # cluster_datamodel only purpose
        # self.subdir = r"damcls/exp2"
        self.config_file = os.path.join(config_dir, "damcls/config_damcls_exp3.ini")  # classify_datamodel
        self.subdir = r"damcls/exp3"
        self.config_data = GagesConfig.set_subdir(self.config_file, self.subdir)
        self.num_cluster = 2
        self.nid_file = 'OH_U.xlsx'

    def test_data_temp_damcls(self):
        config_data_1 = self.config_data
        source_data_1 = GagesSource(config_data_1, config_data_1.model_dict["data"]["tRangeTrain"])
        df1 = DataModel(source_data_1)
        save_datamodel(df1, data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')

    def test_explore_damcls_datamodel(self):
        df = load_datamodel(self.config_data.data_path["Temp"], data_source_file_name='data_source.txt',
                            stat_file_name='Statistics.json', flow_file_name='flow.npy',
                            forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                            f_dict_file_name='dictFactorize.json',
                            var_dict_file_name='dictAttribute.json',
                            t_s_dict_file_name='dictTimeSpace.json')
        # nid_input = NidModel()
        nid_input = NidModel(self.nid_file)
        dam_input = GagesDamDataModel(df, nid_input)
        data_input = GagesExploreDataModel(dam_input.gages_input)
        data_models = data_input.classify_datamodel()
        # data_models = data_input.cluster_datamodel(self.num_cluster, start_dam_var='GAGE_MAIN_DAM_PURPOSE')
        count = 0
        for data_model in data_models:
            print("saving model", str(count + 1), "\n")
            save_datamodel(data_model, data_source_file_name='data_source.txt',
                           stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                           attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                           var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
            count += 1

    def test_explore_damcls(self):
        models_num = 0
        dirs = os.listdir(self.config_data.data_path["Temp"])
        for dir_temp in dirs:
            if os.path.isdir(os.path.join(self.config_data.data_path["Temp"], dir_temp)):
                models_num += 1
        for count in range(models_num):
            print("\n", "training model", str(count + 1), ":\n")
            data_model = load_datamodel(self.config_data.data_path["Temp"], str(count),
                                        data_source_file_name='data_source.txt',
                                        stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                        forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                        f_dict_file_name='dictFactorize.json',
                                        var_dict_file_name='dictAttribute.json',
                                        t_s_dict_file_name='dictTimeSpace.json')
            # temporary treatment for
            ngrid = data_model.data_attr.shape[0]
            nt = data_model.data_flow.shape[1]
            mini_batch = data_model.data_source.data_config.model_dict['train']['miniBatch']
            if 1 - mini_batch[0] * mini_batch[1] / ngrid / nt < 0:
                print("don't train this one")
            else:
                master_train(data_model)
            count += 1

    def test_data_temp_test_damcls(self):
        config_data_test = self.config_data
        source_data_test = GagesSource(config_data_test, config_data_test.model_dict["data"]["tRangeTest"])
        df_test = DataModel(source_data_test)
        save_datamodel(df_test, data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')

    def test_damcls_test_datamodel(self):
        df_test = load_datamodel(self.config_data.data_path["Temp"], data_source_file_name='test_data_source.txt',
                                 stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                 forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                 f_dict_file_name='test_dictFactorize.json',
                                 var_dict_file_name='test_dictAttribute.json',
                                 t_s_dict_file_name='test_dictTimeSpace.json')
        # nid_input = NidModel()
        nid_input = NidModel(self.nid_file)
        dam_input_test = GagesDamDataModel(df_test, nid_input)
        data_input_test = GagesExploreDataModel(dam_input_test.gages_input)
        models_num = 0
        dirs = os.listdir(self.config_data.data_path["Temp"])
        for dir_temp in dirs:
            if os.path.isdir(os.path.join(self.config_data.data_path["Temp"], dir_temp)):
                models_num += 1
        for count in range(models_num):
            print("saving test model", str(count + 1), ":\n")
            data_train_model = load_datamodel(self.config_data.data_path["Temp"], str(count),
                                              data_source_file_name='data_source.txt',
                                              stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                              forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                              f_dict_file_name='dictFactorize.json',
                                              var_dict_file_name='dictAttribute.json',
                                              t_s_dict_file_name='dictTimeSpace.json')
            sites_id_i = data_train_model.t_s_dict["sites_id"]
            f_dict_dam_purpose = data_train_model.f_dict['GAGE_MAIN_DAM_PURPOSE']
            data_test_model = data_input_test.choose_datamodel(sites_id_i, f_dict_dam_purpose, count)
            save_datamodel(data_test_model, data_source_file_name='test_data_source.txt',
                           stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                           forcing_file_name='test_forcing', attr_file_name='test_attr',
                           f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                           t_s_dict_file_name='test_dictTimeSpace.json')
            count += 1

    def test_damcls_test(self):
        models_num = 0
        dirs = os.listdir(self.config_data.data_path["Temp"])
        for dir_temp in dirs:
            if os.path.isdir(os.path.join(self.config_data.data_path["Temp"], dir_temp)):
                models_num += 1
        for count in range(models_num):
            print("\n", "testing model", str(count + 1), ":\n")
            data_model = load_datamodel(self.config_data.data_path["Temp"], str(count),
                                        data_source_file_name='test_data_source.txt',
                                        stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                        forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                        f_dict_file_name='test_dictFactorize.json',
                                        var_dict_file_name='test_dictAttribute.json',
                                        t_s_dict_file_name='test_dictTimeSpace.json')

            model_file = os.path.join(data_model.data_source.data_config.model_dict['dir']['Out'], 'model_Ep' + str(
                data_model.data_source.data_config.model_dict['train']['nEpoch']) + '.pt')
            if os.path.isfile(model_file):
                pred, obs = master_test(data_model)
                pred = pred.reshape(pred.shape[0], pred.shape[1])
                obs = obs.reshape(obs.shape[0], obs.shape[1])
                inds = statError(obs, pred)
                show_me_num = 1
                t_s_dict = data_model.t_s_dict
                sites = np.array(t_s_dict["sites_id"])
                t_range = np.array(t_s_dict["t_final_range"])
                ts_fig = plot_ts_obs_pred(obs, pred, sites, t_range, show_me_num)
                ts_fig.savefig(os.path.join(data_model.data_source.data_config.data_path["Out"], "ts_fig.png"))
                # # plot box，使用seaborn库
                keys = ["Bias", "RMSE", "NSE"]
                inds_test = subset_of_dict(inds, keys)
                box_fig = plot_boxes_inds(inds_test)
                box_fig.savefig(os.path.join(data_model.data_source.data_config.data_path["Out"], "box_fig.png"))
                # plot map
                sites_df = pd.DataFrame({"sites": sites, keys[2]: inds_test[keys[2]]})
                plot_ind_map(data_model.data_source.all_configs['gage_point_file'], sites_df)
            count += 1


if __name__ == '__main__':
    unittest.main()
