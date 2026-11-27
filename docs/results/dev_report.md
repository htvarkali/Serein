# Serein backtest (dev) - 2026-11-23 15:06
code version: 9f01f4d + uncommitted changes
rows: train 130050, val 32300, conf 32300, test 32725; leads [0, 1, 2, 3]
graph: 425 nodes, 4250 edges
features: 65

## training smokecast (seed 0)
  epoch   0 train 0.1628 val 0.1158 *
  epoch   1 train 0.1401 val 0.1111 *
  epoch   3 train 0.1317 val 0.1073 *
  epoch   4 train 0.1262 val 0.1055 *
  epoch   7 train 0.1212 val 0.1024 *
  epoch  10 train 0.1177 val 0.1026
  epoch  11 train 0.1168 val 0.1011 *
  epoch  13 train 0.1144 val 0.1008 *
  epoch  18 train 0.1115 val 0.1002 *
  epoch  20 train 0.1127 val 0.1010
  epoch  23 train 0.1115 val 0.0997 *
  epoch  30 train 0.1067 val 0.1022
  epoch  36 train 0.1031 val 0.0992 *
  epoch  40 train 0.1019 val 0.1008
  epoch  50 train 0.0996 val 0.1042
  epoch  60 train 0.0963 val 0.1029
  early stop at epoch 66; best val 0.0992

## training smokecast (seed 1)
  epoch   0 train 0.1653 val 0.1173 *
  epoch   1 train 0.1472 val 0.1105 *
  epoch   2 train 0.1352 val 0.1085 *
  epoch   3 train 0.1305 val 0.1061 *
  epoch   4 train 0.1288 val 0.1044 *
  epoch   7 train 0.1215 val 0.1013 *
  epoch  10 train 0.1188 val 0.1007 *
  epoch  16 train 0.1140 val 0.0999 *
  epoch  20 train 0.1118 val 0.1004
  epoch  25 train 0.1089 val 0.0989 *
  epoch  27 train 0.1080 val 0.0988 *
  epoch  30 train 0.1061 val 0.0999
  epoch  40 train 0.1055 val 0.1001
  epoch  42 train 0.1010 val 0.0985 *
  epoch  50 train 0.0995 val 0.1005
  epoch  55 train 0.0970 val 0.0983 *
  epoch  60 train 0.0956 val 0.1023
  epoch  70 train 0.0946 val 0.1022
  epoch  80 train 0.0926 val 0.1013
  early stop at epoch 85; best val 0.0983

## training smokecast (seed 2)
  epoch   0 train 0.1623 val 0.1159 *
  epoch   1 train 0.1438 val 0.1119 *
  epoch   2 train 0.1346 val 0.1070 *
  epoch   4 train 0.1290 val 0.1062 *
  epoch   5 train 0.1255 val 0.1053 *
  epoch   6 train 0.1242 val 0.1036 *
  epoch   8 train 0.1195 val 0.1021 *
  epoch   9 train 0.1194 val 0.1013 *
  epoch  10 train 0.1200 val 0.1025
  epoch  15 train 0.1152 val 0.0998 *
  epoch  19 train 0.1138 val 0.0990 *
  epoch  20 train 0.1117 val 0.1002
  epoch  30 train 0.1057 val 0.1015
  epoch  40 train 0.1024 val 0.0992
  epoch  43 train 0.1016 val 0.0988 *
  epoch  50 train 0.0986 val 0.1016
  epoch  60 train 0.0963 val 0.1017
  epoch  70 train 0.0947 val 0.1016
  early stop at epoch 73; best val 0.0988

## training smokecast (seed 3)
  epoch   0 train 0.1636 val 0.1174 *
  epoch   1 train 0.1394 val 0.1088 *
  epoch   2 train 0.1373 val 0.1075 *
  epoch   4 train 0.1272 val 0.1039 *
  epoch   8 train 0.1196 val 0.1021 *
  epoch  10 train 0.1188 val 0.1027
  epoch  12 train 0.1163 val 0.1011 *
  epoch  13 train 0.1155 val 0.1006 *
  epoch  20 train 0.1101 val 0.1007
  epoch  27 train 0.1096 val 0.1005 *
  epoch  30 train 0.1066 val 0.1012
  epoch  32 train 0.1042 val 0.1003 *
  epoch  34 train 0.1049 val 0.0996 *
  epoch  40 train 0.1014 val 0.1024
  epoch  50 train 0.0992 val 0.1022
  epoch  60 train 0.0960 val 0.1022
  early stop at epoch 64; best val 0.0996

## training smokecast (seed 4)
  epoch   0 train 0.1613 val 0.1142 *
  epoch   1 train 0.1403 val 0.1086 *
  epoch   2 train 0.1341 val 0.1083 *
  epoch   3 train 0.1310 val 0.1067 *
  epoch   4 train 0.1263 val 0.1029 *
  epoch  10 train 0.1177 val 0.1021 *
  epoch  11 train 0.1169 val 0.1018 *
  epoch  13 train 0.1147 val 0.0994 *
  epoch  20 train 0.1124 val 0.1010
  epoch  30 train 0.1059 val 0.1015
  epoch  31 train 0.1062 val 0.0993 *
  epoch  40 train 0.1037 val 0.0998
  epoch  50 train 0.0986 val 0.1022
  epoch  60 train 0.0976 val 0.1019
  early stop at epoch 61; best val 0.0993

## training smokecast_nograph (seed 0)
  epoch   0 train 0.1726 val 0.1182 *
  epoch   1 train 0.1409 val 0.1121 *
  epoch   2 train 0.1374 val 0.1094 *
  epoch   3 train 0.1339 val 0.1076 *
  epoch   4 train 0.1292 val 0.1061 *
  epoch   5 train 0.1274 val 0.1050 *
  epoch   6 train 0.1302 val 0.1040 *
  epoch   7 train 0.1256 val 0.1024 *
  epoch  10 train 0.1226 val 0.1021 *
  epoch  13 train 0.1203 val 0.1012 *
  epoch  16 train 0.1197 val 0.1009 *
  epoch  18 train 0.1186 val 0.0999 *
  epoch  20 train 0.1196 val 0.1015
  epoch  23 train 0.1201 val 0.0994 *
  epoch  30 train 0.1159 val 0.0997
  epoch  40 train 0.1139 val 0.1003
  epoch  45 train 0.1144 val 0.0994 *
  epoch  46 train 0.1129 val 0.0989 *
  epoch  50 train 0.1133 val 0.1010
  epoch  60 train 0.1122 val 0.1000
  epoch  70 train 0.1102 val 0.1001
  early stop at epoch 76; best val 0.0989

## training smokecast_nograph (seed 1)
  epoch   0 train 0.1728 val 0.1220 *
  epoch   1 train 0.1487 val 0.1125 *
  epoch   2 train 0.1360 val 0.1070 *
  epoch   3 train 0.1337 val 0.1064 *
  epoch   4 train 0.1313 val 0.1058 *
  epoch   5 train 0.1296 val 0.1046 *
  epoch   6 train 0.1280 val 0.1041 *
  epoch   7 train 0.1254 val 0.1018 *
  epoch   8 train 0.1268 val 0.1018 *
  epoch   9 train 0.1233 val 0.1013 *
  epoch  10 train 0.1231 val 0.1015
  epoch  14 train 0.1203 val 0.1008 *
  epoch  20 train 0.1196 val 0.1002 *
  epoch  23 train 0.1200 val 0.0994 *
  epoch  27 train 0.1172 val 0.0992 *
  epoch  30 train 0.1172 val 0.1004
  epoch  40 train 0.1185 val 0.0994
  epoch  48 train 0.1136 val 0.0992 *
  epoch  50 train 0.1125 val 0.0994
  epoch  56 train 0.1120 val 0.0984 *
  epoch  60 train 0.1121 val 0.1004
  epoch  70 train 0.1108 val 0.1018
  epoch  80 train 0.1108 val 0.0996
  early stop at epoch 86; best val 0.0984

## training smokecast_nograph (seed 2)
  epoch   0 train 0.1705 val 0.1196 *
  epoch   1 train 0.1444 val 0.1111 *
  epoch   2 train 0.1359 val 0.1089 *
  epoch   3 train 0.1329 val 0.1064 *
  epoch   4 train 0.1310 val 0.1052 *
  epoch   6 train 0.1286 val 0.1029 *
  epoch   8 train 0.1246 val 0.1023 *
  epoch  10 train 0.1249 val 0.1033
  epoch  12 train 0.1220 val 0.1012 *
  epoch  15 train 0.1231 val 0.1011 *
  epoch  18 train 0.1229 val 0.1007 *
  epoch  19 train 0.1205 val 0.1004 *
  epoch  20 train 0.1203 val 0.1003 *
  epoch  22 train 0.1194 val 0.0999 *
  epoch  30 train 0.1160 val 0.1007
  epoch  40 train 0.1151 val 0.0997 *
  epoch  41 train 0.1148 val 0.0995 *
  epoch  43 train 0.1142 val 0.0995 *
  epoch  45 train 0.1126 val 0.0993 *
  epoch  50 train 0.1120 val 0.1005
  epoch  60 train 0.1110 val 0.1006
  epoch  70 train 0.1096 val 0.1007
  early stop at epoch 75; best val 0.0993

## training smokecast_nograph (seed 3)
  epoch   0 train 0.1730 val 0.1222 *
  epoch   1 train 0.1417 val 0.1116 *
  epoch   2 train 0.1377 val 0.1081 *
  epoch   4 train 0.1298 val 0.1048 *
  epoch   7 train 0.1266 val 0.1022 *
  epoch  10 train 0.1238 val 0.1022
  epoch  12 train 0.1219 val 0.1021 *
  epoch  13 train 0.1214 val 0.1012 *
  epoch  14 train 0.1220 val 0.1007 *
  epoch  16 train 0.1195 val 0.1002 *
  epoch  20 train 0.1183 val 0.1005
  epoch  22 train 0.1176 val 0.0999 *
  epoch  27 train 0.1185 val 0.0991 *
  epoch  30 train 0.1171 val 0.1008
  epoch  34 train 0.1145 val 0.0991 *
  epoch  40 train 0.1138 val 0.0998
  epoch  50 train 0.1124 val 0.0992
  epoch  57 train 0.1118 val 0.0986 *
  epoch  59 train 0.1109 val 0.0985 *
  epoch  60 train 0.1112 val 0.1001
  epoch  70 train 0.1113 val 0.0999
  epoch  80 train 0.1092 val 0.0997
  early stop at epoch 89; best val 0.0985

## training smokecast_nograph (seed 4)
  epoch   0 train 0.1711 val 0.1185 *
  epoch   1 train 0.1425 val 0.1093 *
  epoch   2 train 0.1354 val 0.1077 *
  epoch   3 train 0.1326 val 0.1066 *
  epoch   4 train 0.1305 val 0.1038 *
  epoch   7 train 0.1255 val 0.1035 *
  epoch   9 train 0.1234 val 0.1033 *
  epoch  10 train 0.1233 val 0.1027 *
  epoch  11 train 0.1232 val 0.1022 *
  epoch  13 train 0.1213 val 0.1022 *
  epoch  15 train 0.1217 val 0.1019 *
  epoch  16 train 0.1204 val 0.1009 *
  epoch  18 train 0.1202 val 0.1006 *
  epoch  20 train 0.1194 val 0.1000 *
  epoch  27 train 0.1182 val 0.1000 *
  epoch  30 train 0.1155 val 0.1020
  epoch  31 train 0.1162 val 0.0997 *
  epoch  40 train 0.1146 val 0.1001
  epoch  45 train 0.1133 val 0.0995 *
  epoch  46 train 0.1126 val 0.0992 *
  epoch  50 train 0.1121 val 0.0992
  epoch  60 train 0.1123 val 0.1000
  epoch  70 train 0.1097 val 0.1008
  early stop at epoch 76; best val 0.0992

## training gbm
warning cut-offs P(>=35.5) tuned on calibration: {0: 0.5500000000000003, 1: 0.4250000000000001, 2: 0.5000000000000002, 3: 0.2750000000000001}

## Results: all site-days
RMSE (µg/m³, lower is better)
lead                     0      1      2      3
model                                          
aqm_bc               10.14  11.02  12.35    NaN
climatology          13.44  13.76  13.81  13.71
gbm                   5.44   8.82  10.99  12.64
hrrr_smoke           12.63   9.05    NaN    NaN
noaa_best            10.14  11.02  12.35  15.48
persistence          10.15  13.79  14.97  15.48
persistence_morning   7.38  14.89    NaN    NaN
smokecast             4.36   7.78   9.72  11.58
smokecast_nograph     4.45   8.20  10.12  12.01

RMSE on smoke-affected days (HMS plume overhead yesterday)
lead                     0      1      2      3
model                                          
aqm_bc               14.77  15.87  17.50    NaN
climatology          19.95  20.12  19.77  19.70
gbm                   8.05  12.77  15.71  18.33
hrrr_smoke           18.75  12.73    NaN    NaN
noaa_best            14.77  15.87  17.50  22.55
persistence          15.03  20.29  21.66  22.55
persistence_morning  10.36  21.51    NaN    NaN
smokecast             6.33  11.04  13.83  16.71
smokecast_nograph     6.47  11.72  14.47  17.40

USG+ critical success index (higher is better)
lead                     0      1      2      3
model                                          
aqm_bc               0.369  0.285  0.142    NaN
climatology          0.000  0.000  0.000  0.000
gbm                  0.641  0.460  0.259  0.089
hrrr_smoke           0.509  0.468    NaN    NaN
noaa_best            0.369  0.285  0.142  0.151
persistence          0.376  0.257  0.179  0.151
persistence_morning  0.501  0.251    NaN    NaN
smokecast            0.656  0.535  0.435  0.287
smokecast_nograph    0.674  0.529  0.403  0.277
smokecast_warnrule   0.665  0.515  0.435  0.273

90% interval coverage (target 0.90)
lead                   0      1      2      3
model                                        
gbm                0.909  0.908  0.901  0.908
smokecast          0.904  0.893  0.901  0.909
smokecast_nograph  0.905  0.895  0.903  0.913

Head-to-head (same rows; skill = 1 - RMSE_smokecast/RMSE_baseline; CI = 95% day-bootstrap of RMSE diff)
 lead                  vs     n  rmse_smokecast  rmse_baseline  skill   ci_lo  ci_hi
    0           noaa_best 25030           4.362         10.138  0.570  -8.468 -3.299
    0              aqm_bc 25030           4.362         10.138  0.570  -8.468 -3.299
    0          hrrr_smoke 25030           4.362         12.630  0.655 -12.970 -4.041
    0         persistence 24732           4.379         10.149  0.569  -8.537 -2.726
    0 persistence_morning 25030           4.362          7.378  0.409  -3.866 -2.181
    0                 gbm 25030           4.362          5.444  0.199  -1.954 -0.183
    0   smokecast_nograph 25030           4.362          4.454  0.021  -0.346  0.109
    1           noaa_best 25041           7.776         11.022  0.294  -4.599 -1.754
    1              aqm_bc 25041           7.776         11.022  0.294  -4.599 -1.754
    1          hrrr_smoke 25041           7.776          9.053  0.141  -2.140 -0.466
    1         persistence 24562           7.738         13.795  0.439  -9.097 -2.881
    1 persistence_morning 24897           7.786         14.892  0.477  -9.589 -4.458
    1                 gbm 25041           7.776          8.824  0.119  -2.099 -0.017
    1   smokecast_nograph 25041           7.776          8.199  0.052  -0.751 -0.089
    2           noaa_best 24730           9.721         12.348  0.213  -3.782 -1.479
    2              aqm_bc 24730           9.721         12.348  0.213  -3.782 -1.479
    2         persistence 24144           9.508         14.965  0.365  -7.794 -3.164
    2                 gbm 24730           9.721         10.989  0.115  -2.298  0.003
    2   smokecast_nograph 24730           9.721         10.125  0.040  -0.970  0.006
    3           noaa_best 23787          11.398         15.475  0.263  -6.964 -1.756
    3         persistence 23787          11.398         15.475  0.263  -6.964 -1.756
    3                 gbm 24432          11.584         12.640  0.084  -2.063  0.068
    3   smokecast_nograph 24432          11.584         12.014  0.036  -0.704 -0.132

vs. official EPA AQI forecast (reporting areas, category scores)
 lead          who  n_area_days  cat_acc  usg_events  usg_pod  usg_far  usg_csi
    0    smokecast        10948    0.928         224    0.777    0.167    0.672
    0 epa_forecast        10948    0.842         224    0.665    0.402    0.460
    1    smokecast        10775    0.881         244    0.717    0.345    0.521
    1 epa_forecast        10775    0.827         244    0.459    0.467    0.327
    2    smokecast         6631    0.895         190    0.616    0.291    0.492
    2 epa_forecast         6631    0.855         190    0.368    0.340    0.310
    3    smokecast         5576    0.895         118    0.483    0.584    0.288
    3 epa_forecast         5576    0.885         118    0.110    0.316    0.105