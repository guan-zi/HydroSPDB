from hydroDL import pathSMAP
from hydroDL.master import default, wrapMaster, train, runTrain
import os

cDir = os.path.dirname(os.path.abspath(__file__))
cDir = r'/mnt/sdc/SUR_VIC/'

# define training options
optData = default.update(
    default.optDataSMAP,
    rootDB='/mnt/sdc/SUR_VIC/input_VIC/',
    varT=[
    'APCP_FORA', 'DLWRF_FORA', 'DSWRF_FORA', 'TMP_2_FORA', 'SPFH_2_FORA',
    'VGRD_10_FORA', 'UGRD_10_FORA', 'PEVAP_FORA', 'PRES_FORA'
],
    varC=[
    'DEPTH_1', 'DEPTH_2', 'DEPTH_3', 'Ds', 'Ds_MAX', 'EXPT_1', 'EXPT_2', 'EXPT_3',
    'INFILT', 'Ws'
],
    target=['SOILM_lev1_VIC', 'SSRUN_VIC','EVP_VIC'],
    # target='SOILM_0-100_VIC',
    subset='CONUS_VICv16f1',
    tRange=[20150401, 20160401])
optModel = default.optLstm
optLoss = default.optLossRMSE
optTrain = default.update(default.optTrainSMAP, miniBatch=[100,60], nEpoch=100)
out = os.path.join(cDir, 'multiOutput_CONUSv16f1_VIC/CONUS_v16f1_SSRUN_EVP_SOILM_lev1')
masterDict = wrapMaster(out, optData, optModel, optLoss, optTrain)

# train
train(masterDict)
# runTrain(masterDict, cudaID=2, screen='LSTM-multi')
