from collections import OrderedDict
from hydroDL.data import camels, gages2

# Gages2 default options
optDataGages2 = OrderedDict(
    name='hydroDL.data.gages2.DataframeGages2',
    subset='All',
    varT=gages2.FORCING_LST,
    varC=gages2.ATTR_STR_SEL,
    target=['streamflowTest'],
    tRange=gages2.tRangeTrain,
    doNorm=[True, True],
    rmNan=[True, False],
    daObs=0)
optTrainGages2 = OrderedDict(miniBatch=[100, 200], nEpoch=10, saveEpoch=1)
# Streamflow default options
optDataCamels = OrderedDict(
    name='hydroDL.data.camels.DataframeCamels',
    subset='All',
    varT=camels.forcingLst,
    varC=camels.attrLstSel,
    target=['streamflowTest'],
    tRange=[19900101, 19950101],
    doNorm=[True, True],
    rmNan=[True, False],
    daObs=0)
optTrainCamels = OrderedDict(miniBatch=[100, 200], nEpoch=1000, saveEpoch=100)

""" model options """
optLstmGages2 = OrderedDict(
    name='hydroDL.model.rnn.CudnnLstmModel',
    nx=len(optDataGages2['varT']) + len(optDataGages2['varC']),
    ny=1,
    hiddenSize=256,
    doReLU=True)
optLstmCamels = OrderedDict(
    name='hydroDL.model.rnn.CudnnLstmModel',
    nx=len(optDataCamels['varT']) + len(optDataCamels['varC']),
    ny=1,
    hiddenSize=256,
    doReLU=True)
optLossRMSE = OrderedDict(name='hydroDL.model.crit.RmseLoss', prior='gauss')
optLossSigma = OrderedDict(name='hydroDL.model.crit.SigmaLoss', prior='gauss')


def update(opt, **kw):
    for key in kw:
        if key in opt:
            try:
                opt[key] = type(opt[key])(kw[key])
            except ValueError:
                print('skiped ' + key + ': wrong type')
        else:
            print('skiped ' + key + ': not in argument dict')
    return opt
