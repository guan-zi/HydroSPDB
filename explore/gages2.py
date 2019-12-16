"""read gages-ii data以计算统计值 and ready for model 的脚本代码，
some scripts for config of gages-ii datasets"""

# 读取GAGES-II数据需要指定文件路径、时间范围、属性类型、需要计算配置的项是forcing data。
# module variable
import json
import os

import pandas as pd

from data.input_data import cal_stat_all
from data.source_data import usgs_screen_streamflow, read_gage_info, read_usgs
from hydroDL import pathGages2
from hydroDL import utils

dirDB = pathGages2['DB']

# USGS所有站点 file
GAGE_FILE = os.path.join(dirDB, 'basinchar_and_report_sept_2011', 'spreadsheets-in-csv-format',
                         'conterm_basinid.txt')
GAGE_SHAPE_DIR = os.path.join(dirDB, 'boundaries-shapefiles-by-aggeco')

GAGE_FLD_LST = ['STAID', 'STANAME', 'DRAIN_SQKM', 'HUC02', 'LAT_GAGE', 'LNG_GAGE', 'STATE', 'BOUND_SOURCE', 'HCDN-2009',
                'HBN36', 'OLD_HCDN', 'NSIP_SENTINEL', 'FIPS_SITE', 'COUNTYNAME_SITE', 'NAWQA_SUID']
# gageFldLst = camels.gageFldLst
DIR_GAGE_FLOW = os.path.join(dirDB, 'gages_streamflow')
DIR_GAGE_ATTR = os.path.join(dirDB, 'basinchar_and_report_sept_2011', 'spreadsheets-in-csv-format')
STREAMFLOW_URL = 'https://waterdata.usgs.gov/nwis/dv?cb_00060=on&format=rdb&site_no={' \
                 '}&referred_module=sw&period=&begin_date={}-{}-{}&end_date={}-{}-{} '

# 671个流域的forcing值需要重新计算，但是训练先用着671个流域，可以先用CAMELS的计算。
FORCING_LST = ['dayl', 'prcp', 'srad', 'swe', 'tmax', 'tmin', 'vp']

# all attributes:
# attrLstAll = os.listdir(DIR_GAGE_ATTR)
# # 因为是对CONUS分析，所以只用conterm开头的
# ATTR_LST = []
# for attrLstAllTemp in attrLstAll:
#     if 'conterm' in attrLstAllTemp:
#         attrLstTemp = attrLstAllTemp[8:].lower()
#         ATTR_LST.append(attrLstTemp)

# gages的attributes可以先按照CAMELS的这几项去找，因为使用了forcing数据，因此attributes里就没用气候的数据，因为要进行预测，所以也没用水文的
# land cover部分：forest_frac对应FORESTNLCD06；lai没有，这里暂时用所有forest的属性；land_cover暂时用除人为种植之外的其他所有属性。
# soil：soil_depth相关的有：ROCKDEPAVE；soil_porosity类似的可能是：AWCAVE；soil_conductivity可能相关的：PERMAVE；max_water_content没有，暂时用RFACT
# geology在GAGES-II中一共两类，来自两个数据源，用第一种，
attrBasin = ['ELEV_MEAN_M_BASIN', 'SLOPE_PCT', 'DRAIN_SQKM']
attrLandcover = ['FORESTNLCD06', 'BARRENNLCD06', 'DECIDNLCD06', 'EVERGRNLCD06', 'MIXEDFORNLCD06', 'SHRUBNLCD06',
                 'GRASSNLCD06', 'WOODYWETNLCD06', 'EMERGWETNLCD06']
attrSoil = ['ROCKDEPAVE', 'AWCAVE', 'PERMAVE', 'RFACT', ]
attrGeol = ['GEOL_REEDBUSH_DOM', 'GEOL_REEDBUSH_DOM_PCT', 'GEOL_REEDBUSH_SITE']
# attributes include: Hydro, HydroMod_Dams, HydroMod_Other,Landscape_Pat,
# LC06_Basin,LC06_Mains100,LC06_Mains800,LC06_Rip100,LC_Crops,Pop_Infrastr,Prot_Areas
attrHydro = ['STREAMS_KM_SQ_KM', 'STRAHLER_MAX', 'MAINSTEM_SINUOUSITY', 'REACHCODE', 'ARTIFPATH_PCT',
             'ARTIFPATH_MAINSTEM_PCT', 'HIRES_LENTIC_PCT', 'BFI_AVE', 'PERDUN', 'PERHOR', 'TOPWET', 'CONTACT']
# 'RUNAVE7100', 'WB5100_JAN_MM', 'WB5100_FEB_MM', 'WB5100_MAR_MM', 'WB5100_APR_MM', 'WB5100_MAY_MM',
# 'WB5100_JUN_MM', 'WB5100_JUL_MM', 'WB5100_AUG_MM', 'WB5100_SEP_MM', 'WB5100_OCT_MM', 'WB5100_NOV_MM',
# 'WB5100_DEC_MM', 'WB5100_ANN_MM', 'PCT_1ST_ORDER', 'PCT_2ND_ORDER', 'PCT_3RD_ORDER', 'PCT_4TH_ORDER',
# 'PCT_5TH_ORDER', 'PCT_6TH_ORDER_OR_MORE', 'PCT_NO_ORDER'
# "pre19xx" attributes need be given to right period
attrHydroModDams = ['NDAMS_2009', 'DDENS_2009', 'STOR_NID_2009', 'STOR_NOR_2009', 'MAJ_NDAMS_2009', 'MAJ_DDENS_2009',
                    'RAW_DIS_NEAREST_DAM', 'RAW_AVG_DIS_ALLDAMS', 'RAW_DIS_NEAREST_MAJ_DAM', 'RAW_AVG_DIS_ALL_MAJ_DAMS']
# 'pre1940_NDAMS', 'pre1950_NDAMS', 'pre1960_NDAMS', 'pre1970_NDAMS', 'pre1980_NDAMS',
#                     'pre1990_NDAMS', 'pre1940_DDENS', 'pre1950_DDENS', 'pre1960_DDENS', 'pre1970_DDENS',
#                     'pre1980_DDENS', 'pre1990_DDENS', 'pre1940_STOR', 'pre1950_STOR', 'pre1960_STOR', 'pre1970_STOR',
#                     'pre1980_STOR', 'pre1990_STOR',
attrHydroModOther = ['CANALS_PCT', 'RAW_DIS_NEAREST_CANAL', 'RAW_AVG_DIS_ALLCANALS', 'CANALS_MAINSTEM_PCT',
                     'NPDES_MAJ_DENS', 'RAW_DIS_NEAREST_MAJ_NPDES', 'RAW_AVG_DIS_ALL_MAJ_NPDES', 'FRESHW_WITHDRAWAL',
                     'MINING92_PCT', 'PCT_IRRIG_AG', 'POWER_NUM_PTS', 'POWER_SUM_MW']
attrLandscapePat = ['FRAGUN_BASIN', 'HIRES_LENTIC_NUM', 'HIRES_LENTIC_DENS', 'HIRES_LENTIC_MEANSIZ']
attrLC06Basin = ['DEVNLCD06', 'FORESTNLCD06', 'PLANTNLCD06', 'WATERNLCD06', 'SNOWICENLCD06', 'DEVOPENNLCD06',
                 'DEVLOWNLCD06', 'DEVMEDNLCD06', 'DEVHINLCD06', 'BARRENNLCD06', 'DECIDNLCD06', 'EVERGRNLCD06',
                 'MIXEDFORNLCD06', 'SHRUBNLCD06', 'GRASSNLCD06', 'PASTURENLCD06', 'CROPSNLCD06', 'WOODYWETNLCD06',
                 'EMERGWETNLCD06']
attrLC06Mains100 = ['MAINS100_DEV', 'MAINS100_FOREST', 'MAINS100_PLANT', 'MAINS100_11', 'MAINS100_12', 'MAINS100_21',
                    'MAINS100_22', 'MAINS100_23', 'MAINS100_24', 'MAINS100_31', 'MAINS100_41', 'MAINS100_42',
                    'MAINS100_43', 'MAINS100_52', 'MAINS100_71', 'MAINS100_81', 'MAINS100_82', 'MAINS100_90',
                    'MAINS100_95', ]
attrLC06Mains800 = ['MAINS800_DEV', 'MAINS800_FOREST', 'MAINS800_PLANT', 'MAINS800_11', 'MAINS800_12', 'MAINS800_21',
                    'MAINS800_22', 'MAINS800_23', 'MAINS800_24', 'MAINS800_31', 'MAINS800_41', 'MAINS800_42',
                    'MAINS800_43', 'MAINS800_52', 'MAINS800_71', 'MAINS800_81', 'MAINS800_82', 'MAINS800_90',
                    'MAINS800_95']
attrLC06Rip100 = ['RIP100_DEV', 'RIP100_FOREST', 'RIP100_PLANT', 'RIP100_11', 'RIP100_12', 'RIP100_21', 'RIP100_22',
                  'RIP100_23', 'RIP100_24', 'RIP100_31', 'RIP100_41', 'RIP100_42', 'RIP100_43', 'RIP100_52',
                  'RIP100_71', 'RIP100_81', 'RIP100_82', 'RIP100_90', 'RIP100_95']
attrLCCrops = ['RIP800_DEV', 'RIP800_FOREST', 'RIP800_PLANT', 'RIP800_11', 'RIP800_12', 'RIP800_21', 'RIP800_22',
               'RIP800_23', 'RIP800_24', 'RIP800_31', 'RIP800_41', 'RIP800_42', 'RIP800_43', 'RIP800_52', 'RIP800_71',
               'RIP800_81', 'RIP800_82', 'RIP800_90', 'RIP800_95']
attrPopInfrastr = ['CDL_CORN', 'CDL_COTTON', 'CDL_RICE', 'CDL_SORGHUM', 'CDL_SOYBEANS', 'CDL_SUNFLOWERS', 'CDL_PEANUTS',
                   'CDL_BARLEY', 'CDL_DURUM_WHEAT', 'CDL_SPRING_WHEAT', 'CDL_WINTER_WHEAT', 'CDL_WWHT_SOY_DBL_CROP',
                   'CDL_OATS', 'CDL_ALFALFA', 'CDL_OTHER_HAYS', 'CDL_DRY_BEANS', 'CDL_POTATOES', 'CDL_FALLOW_IDLE',
                   'CDL_PASTURE_GRASS', 'CDL_ORANGES', 'CDL_OTHER_CROPS', 'CDL_ALL_OTHER_LAND']
attrProtAreas = ['PDEN_2000_BLOCK', 'PDEN_DAY_LANDSCAN_2007', 'PDEN_NIGHT_LANDSCAN_2007', 'ROADS_KM_SQ_KM',
                 'RD_STR_INTERS', 'IMPNLCD06', 'NLCD01_06_DEV']
# firstly don't use all attributes
ATTR_STR_SEL = attrBasin + attrLandcover + attrSoil + attrGeol + attrHydro + attrHydroModDams + attrHydroModOther
# + attrLandscapePat + attrLC06Basin + attrLC06Mains100 + attrLC06Mains800 + attrLC06Rip100 + attrLCCrops + \
# attrPopInfrastr + attrProtAreas

# GAGES-II的所有站点 and all time, for first using of this code to download streamflow datasets
tRange4DownloadData = [19800101, 20150101]  # 左闭右开
tLstAll = utils.time.tRange2Array(tRange4DownloadData)
# gageDict = read_gage_info(gageField)

# training time range
tRangeTrain = [19950101, 20000101]

# regions
# TODO: now just for one region
REF_NONREF_REGIONS = ['bas_nonref_CntlPlains']
REF_NONREF_REGIONS_SHPFILES_DIR = "gagesII_basin_shapefile_wgs84"
GAGESII_POINTS_DIR = "gagesII_9322_point_shapefile"
GAGESII_POINTS_FILE = "gagesII_9322_sept30_2011.shp"
HUC4_SHP_DIR = "huc4"
HUC4_SHP_FILE = "HUC4.shp"

# 为了便于后续的归一化计算，这里需要计算流域attributes、forcings和streamflows统计值。
# module variable
statFile = os.path.join(dirDB, 'Statistics.json')
gageDictOrigin = read_gage_info(GAGE_FILE, region_shapefiles=REF_NONREF_REGIONS, screen_basin_area='HUC4')
# screen some sites
usgs = read_usgs(gageDictOrigin, tRange4DownloadData)
usgsFlow, gagesChosen = usgs_screen_streamflow(
    pd.DataFrame(usgs, index=gageDictOrigin[GAGE_FLD_LST[0]], columns=tLstAll),
    time_range=tRangeTrain, missing_data_ratio=0.1, zero_value_ratio=0.005)
# after screening, update the gageDict and idLst
gageDict = read_gage_info(GAGE_FILE, region_shapefiles=REF_NONREF_REGIONS, ids_specific=gagesChosen)
# 如果统计值已经计算过了，就没必要再重新计算了
if not os.path.isfile(statFile):
    cal_stat_all(gageDict, tRangeTrain, FORCING_LST, usgsFlow, REF_NONREF_REGIONS)
# 计算过了，就从存储的json文件中读取出统计结果
with open(statFile, 'r') as fp:
    statDict = json.load(fp)