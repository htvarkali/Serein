# Serein backtest (dev) - 2026-11-27 01:17
code version: 30a1690 + uncommitted changes
rows: train 130050, val 32300, conf 32300, test 32725; leads [0, 1, 2, 3]
graph: 425 nodes, 4250 edges
features: 65
leave-sites-out: 85 of 425 monitors hidden

## training smokecast (seed 0)
  epoch   0 train 0.1654 val 0.1158 *
  epoch   1 train 0.1423 val 0.1121 *
  epoch   3 train 0.1347 val 0.1071 *
  epoch   4 train 0.1281 val 0.1053 *
  epoch   7 train 0.1235 val 0.1022 *
  epoch  10 train 0.1201 val 0.1023
  epoch  11 train 0.1190 val 0.1011 *
  epoch  13 train 0.1163 val 0.1007 *
  epoch  18 train 0.1132 val 0.1002 *
  epoch  20 train 0.1145 val 0.1007
  epoch  23 train 0.1140 val 0.0991 *
  epoch  30 train 0.1105 val 0.1016
  epoch  40 train 0.1033 val 0.1010
  epoch  50 train 0.1021 val 0.1028
  early stop at epoch 53; best val 0.0991

## training smokecast (seed 1)
  epoch   0 train 0.1672 val 0.1177 *
  epoch   1 train 0.1491 val 0.1106 *
  epoch   2 train 0.1371 val 0.1092 *
  epoch   3 train 0.1326 val 0.1067 *
  epoch   4 train 0.1305 val 0.1047 *
  epoch   7 train 0.1233 val 0.1016 *
  epoch   8 train 0.1234 val 0.1015 *
  epoch  10 train 0.1205 val 0.1001 *
  epoch  16 train 0.1156 val 0.0996 *
  epoch  20 train 0.1131 val 0.0994 *
  epoch  23 train 0.1117 val 0.0992 *
  epoch  25 train 0.1103 val 0.0990 *
  epoch  27 train 0.1093 val 0.0989 *
  epoch  30 train 0.1077 val 0.1004
  epoch  36 train 0.1056 val 0.0985 *
  epoch  40 train 0.1076 val 0.1014
  epoch  50 train 0.1002 val 0.1018
  epoch  60 train 0.0974 val 0.1028
  early stop at epoch 66; best val 0.0985

## training smokecast (seed 2)
  epoch   0 train 0.1644 val 0.1168 *
  epoch   1 train 0.1456 val 0.1124 *
  epoch   2 train 0.1367 val 0.1076 *
  epoch   4 train 0.1311 val 0.1070 *
  epoch   5 train 0.1273 val 0.1057 *
  epoch   6 train 0.1268 val 0.1038 *
  epoch   8 train 0.1214 val 0.1011 *
  epoch  10 train 0.1229 val 0.1023
  epoch  12 train 0.1184 val 0.1010 *
  epoch  15 train 0.1176 val 0.0997 *
  epoch  16 train 0.1154 val 0.0995 *
  epoch  19 train 0.1156 val 0.0991 *
  epoch  20 train 0.1143 val 0.0997
  epoch  30 train 0.1070 val 0.1003
  epoch  40 train 0.1045 val 0.0989 *
  epoch  50 train 0.1000 val 0.1023
  epoch  60 train 0.0978 val 0.1010
  epoch  70 train 0.0956 val 0.1020
  early stop at epoch 70; best val 0.0989

## training smokecast (seed 3)
  epoch   0 train 0.1658 val 0.1176 *
  epoch   1 train 0.1418 val 0.1097 *
  epoch   2 train 0.1399 val 0.1076 *
  epoch   4 train 0.1294 val 0.1043 *
  epoch   5 train 0.1261 val 0.1035 *
  epoch   8 train 0.1216 val 0.1018 *
  epoch  10 train 0.1215 val 0.1041
  epoch  12 train 0.1181 val 0.1014 *
  epoch  13 train 0.1180 val 0.1012 *
  epoch  20 train 0.1120 val 0.1003 *
  epoch  27 train 0.1113 val 0.1001 *
  epoch  30 train 0.1088 val 0.1022
  epoch  34 train 0.1057 val 0.1000 *
  epoch  40 train 0.1052 val 0.1037
  epoch  47 train 0.1016 val 0.0992 *
  epoch  50 train 0.1008 val 0.1015
  epoch  60 train 0.0970 val 0.1048
  epoch  70 train 0.0953 val 0.1033
  early stop at epoch 77; best val 0.0992

## training smokecast (seed 4)
  epoch   0 train 0.1636 val 0.1150 *
  epoch   1 train 0.1424 val 0.1092 *
  epoch   2 train 0.1363 val 0.1087 *
  epoch   3 train 0.1330 val 0.1071 *
  epoch   4 train 0.1286 val 0.1035 *
  epoch   9 train 0.1217 val 0.1032 *
  epoch  10 train 0.1195 val 0.1019 *
  epoch  11 train 0.1193 val 0.1014 *
  epoch  13 train 0.1169 val 0.0989 *
  epoch  20 train 0.1137 val 0.1010
  epoch  28 train 0.1107 val 0.0986 *
  epoch  30 train 0.1073 val 0.1015
  epoch  40 train 0.1051 val 0.0995
  epoch  50 train 0.1009 val 0.1011
  early stop at epoch 58; best val 0.0986

## training smokecast_nograph (seed 0)
  epoch   0 train 0.1751 val 0.1189 *
  epoch   1 train 0.1428 val 0.1130 *
  epoch   2 train 0.1394 val 0.1097 *
  epoch   3 train 0.1355 val 0.1081 *
  epoch   4 train 0.1311 val 0.1064 *
  epoch   5 train 0.1292 val 0.1053 *
  epoch   6 train 0.1320 val 0.1045 *
  epoch   7 train 0.1274 val 0.1027 *
  epoch  10 train 0.1242 val 0.1023 *
  epoch  13 train 0.1221 val 0.1014 *
  epoch  16 train 0.1216 val 0.1011 *
  epoch  18 train 0.1202 val 0.1003 *
  epoch  20 train 0.1213 val 0.1020
  epoch  23 train 0.1220 val 0.0996 *
  epoch  30 train 0.1175 val 0.1001
  epoch  40 train 0.1156 val 0.1008
  epoch  46 train 0.1141 val 0.0992 *
  epoch  50 train 0.1148 val 0.1012
  epoch  60 train 0.1134 val 0.1008
  epoch  70 train 0.1116 val 0.1003
  early stop at epoch 76; best val 0.0992

## training smokecast_nograph (seed 1)
  epoch   0 train 0.1747 val 0.1225 *
  epoch   1 train 0.1506 val 0.1129 *
  epoch   2 train 0.1378 val 0.1076 *
  epoch   3 train 0.1354 val 0.1073 *
  epoch   4 train 0.1330 val 0.1064 *
  epoch   5 train 0.1315 val 0.1049 *
  epoch   6 train 0.1298 val 0.1047 *
  epoch   7 train 0.1273 val 0.1024 *
  epoch   8 train 0.1285 val 0.1021 *
  epoch   9 train 0.1251 val 0.1019 *
  epoch  10 train 0.1248 val 0.1016 *
  epoch  14 train 0.1220 val 0.1012 *
  epoch  20 train 0.1215 val 0.1007 *
  epoch  23 train 0.1219 val 0.0999 *
  epoch  27 train 0.1189 val 0.0995 *
  epoch  30 train 0.1189 val 0.1010
  epoch  40 train 0.1204 val 0.0999
  epoch  50 train 0.1141 val 0.0995
  epoch  55 train 0.1130 val 0.0994 *
  epoch  56 train 0.1133 val 0.0986 *
  epoch  60 train 0.1136 val 0.1006
  epoch  70 train 0.1123 val 0.1023
  epoch  80 train 0.1123 val 0.0997
  early stop at epoch 86; best val 0.0986

## training smokecast_nograph (seed 2)
  epoch   0 train 0.1723 val 0.1202 *
  epoch   1 train 0.1465 val 0.1119 *
  epoch   2 train 0.1377 val 0.1091 *
  epoch   3 train 0.1347 val 0.1070 *
  epoch   4 train 0.1330 val 0.1056 *
  epoch   6 train 0.1306 val 0.1034 *
  epoch   8 train 0.1261 val 0.1027 *
  epoch  10 train 0.1266 val 0.1037
  epoch  12 train 0.1238 val 0.1016 *
  epoch  18 train 0.1248 val 0.1013 *
  epoch  19 train 0.1223 val 0.1009 *
  epoch  20 train 0.1220 val 0.1008 *
  epoch  21 train 0.1202 val 0.1006 *
  epoch  22 train 0.1210 val 0.1003 *
  epoch  30 train 0.1177 val 0.1015
  epoch  40 train 0.1169 val 0.0999 *
  epoch  45 train 0.1143 val 0.0997 *
  epoch  50 train 0.1134 val 0.1011
  epoch  60 train 0.1122 val 0.1010
  epoch  70 train 0.1111 val 0.1014
  early stop at epoch 75; best val 0.0997

## training smokecast_nograph (seed 3)
  epoch   0 train 0.1753 val 0.1222 *
  epoch   1 train 0.1436 val 0.1120 *
  epoch   2 train 0.1394 val 0.1087 *
  epoch   3 train 0.1365 val 0.1086 *
  epoch   4 train 0.1317 val 0.1055 *
  epoch   5 train 0.1293 val 0.1052 *
  epoch   7 train 0.1285 val 0.1027 *
  epoch  10 train 0.1257 val 0.1027
  epoch  11 train 0.1247 val 0.1027 *
  epoch  12 train 0.1239 val 0.1024 *
  epoch  13 train 0.1233 val 0.1013 *
  epoch  14 train 0.1237 val 0.1009 *
  epoch  16 train 0.1211 val 0.1003 *
  epoch  20 train 0.1199 val 0.1006
  epoch  22 train 0.1196 val 0.1001 *
  epoch  27 train 0.1199 val 0.0994 *
  epoch  30 train 0.1188 val 0.1007
  epoch  40 train 0.1151 val 0.0998
  epoch  50 train 0.1137 val 0.0998
  epoch  55 train 0.1131 val 0.0994 *
  epoch  57 train 0.1130 val 0.0992 *
  epoch  59 train 0.1124 val 0.0986 *
  epoch  60 train 0.1124 val 0.1005
  epoch  70 train 0.1122 val 0.1003
  epoch  80 train 0.1102 val 0.1002
  early stop at epoch 89; best val 0.0986

## training smokecast_nograph (seed 4)
  epoch   0 train 0.1735 val 0.1192 *
  epoch   1 train 0.1444 val 0.1097 *
  epoch   2 train 0.1373 val 0.1082 *
  epoch   3 train 0.1344 val 0.1069 *
  epoch   4 train 0.1323 val 0.1043 *
  epoch   7 train 0.1271 val 0.1039 *
  epoch   9 train 0.1251 val 0.1036 *
  epoch  10 train 0.1249 val 0.1029 *
  epoch  11 train 0.1249 val 0.1022 *
  epoch  15 train 0.1233 val 0.1021 *
  epoch  16 train 0.1219 val 0.1011 *
  epoch  18 train 0.1219 val 0.1009 *
  epoch  20 train 0.1208 val 0.1004 *
  epoch  27 train 0.1200 val 0.1002 *
  epoch  30 train 0.1172 val 0.1025
  epoch  31 train 0.1179 val 0.1000 *
  epoch  40 train 0.1164 val 0.1004
  epoch  42 train 0.1161 val 0.0998 *
  epoch  45 train 0.1151 val 0.0993 *
  epoch  50 train 0.1136 val 0.0992 *
  epoch  59 train 0.1137 val 0.0990 *
  epoch  60 train 0.1137 val 0.1002
  epoch  70 train 0.1113 val 0.1012
  epoch  80 train 0.1108 val 0.1002
  early stop at epoch 89; best val 0.0990
warning cut-offs P(>=35.5) tuned on calibration: {0: 0.4000000000000001, 1: 0.4500000000000001, 2: 0.5000000000000002, 3: 0.4250000000000001}

## Results: all site-days
RMSE (µg/m³, lower is better)
lead                     0      1      2      3
model                                          
aqm_bc               10.14  11.02  12.35    NaN
climatology          13.61  14.00  14.15  14.10
hrrr_smoke           12.64   9.06    NaN    NaN
noaa_best            10.14  11.02  12.35  15.48
persistence          10.15  13.79  14.97  15.48
persistence_morning   7.38  14.89    NaN    NaN
smokecast             5.17   8.02   9.79  11.46
smokecast_nograph     5.50   8.19  10.18  12.45

RMSE on smoke-affected days (HMS plume overhead yesterday)
lead                     0      1      2      3
model                                          
aqm_bc               14.77  15.87  17.50    NaN
climatology          20.07  20.45  20.20  20.14
hrrr_smoke           18.76  12.73    NaN    NaN
noaa_best            14.77  15.87  17.50  22.55
persistence          15.03  20.29  21.66  22.55
persistence_morning  10.36  21.51    NaN    NaN
smokecast             7.52  11.35  13.93  16.52
smokecast_nograph     8.04  11.68  14.53  18.02

RMSE at HIDDEN monitors (no readings; persistence/climatology use data a real unmonitored place would not have)
lead                     0      1      2      3
model                                          
aqm_bc               10.46  11.14  11.93    NaN
hrrr_smoke            9.21  10.13    NaN    NaN
noaa_best            10.46  11.14  11.93  14.10
persistence          10.00  13.45  13.46  14.10
persistence_morning   6.78  15.04    NaN    NaN
smokecast             6.99   8.53  10.05  11.52
smokecast_nograph     8.49   8.93  10.51  13.74

USG+ critical success index (higher is better)
lead                     0      1      2      3
model                                          
aqm_bc               0.369  0.285  0.142    NaN
climatology          0.000  0.000  0.000  0.000
hrrr_smoke           0.507  0.472    NaN    NaN
noaa_best            0.369  0.285  0.142  0.151
persistence          0.376  0.257  0.179  0.151
persistence_morning  0.501  0.251    NaN    NaN
smokecast            0.628  0.498  0.435  0.314
smokecast_nograph    0.659  0.530  0.412  0.274
smokecast_warnrule   0.623  0.501  0.435  0.314

90% interval coverage (target 0.90)
lead                   0      1      2      3
model                                        
smokecast          0.894  0.890  0.900  0.908
smokecast_nograph  0.899  0.894  0.904  0.911

Head-to-head (same rows; skill = 1 - RMSE_smokecast/RMSE_baseline; CI = 95% day-bootstrap of RMSE diff)
 lead                  vs     n  rmse_smokecast  rmse_baseline  skill   ci_lo  ci_hi
    0           noaa_best 25030           5.166         10.138  0.490  -7.145 -2.926
    0              aqm_bc 25030           5.166         10.138  0.490  -7.145 -2.926
    0          hrrr_smoke 25030           5.166         12.643  0.591 -12.234 -3.305
    0         persistence 24732           5.183         10.149  0.489  -7.549 -2.181
    0 persistence_morning 25030           5.166          7.378  0.300  -2.839 -1.508
    0   smokecast_nograph 25030           5.166          5.498  0.060  -0.656 -0.062
    1           noaa_best 25041           8.016         11.022  0.273  -4.386 -1.530
    1              aqm_bc 25041           8.016         11.022  0.273  -4.386 -1.530
    1          hrrr_smoke 25041           8.016          9.061  0.115  -2.162 -0.025
    1         persistence 24562           7.974         13.795  0.422  -8.998 -2.644
    1 persistence_morning 24897           8.026         14.892  0.461  -9.442 -4.271
    1   smokecast_nograph 25041           8.016          8.189  0.021  -0.475  0.077
    2           noaa_best 24730           9.791         12.348  0.207  -3.733 -1.539
    2              aqm_bc 24730           9.791         12.348  0.207  -3.733 -1.539
    2         persistence 24144           9.584         14.965  0.360  -7.734 -3.166
    2   smokecast_nograph 24730           9.791         10.177  0.038  -0.836 -0.038
    3           noaa_best 23787          11.294         15.475  0.270  -7.087 -1.877
    3         persistence 23787          11.294         15.475  0.270  -7.087 -1.877
    3   smokecast_nograph 24432          11.462         12.451  0.079  -1.868 -0.416

vs. official EPA AQI forecast (reporting areas, category scores)
 lead          who  n_area_days  cat_acc  usg_events  usg_pod  usg_far  usg_csi
    0    smokecast        10948    0.918         224    0.790    0.217    0.648
    0 epa_forecast        10948    0.842         224    0.665    0.402    0.460
    1    smokecast        10775    0.878         244    0.697    0.356    0.503
    1 epa_forecast        10775    0.827         244    0.459    0.467    0.327
    2    smokecast         6631    0.894         190    0.605    0.281    0.489
    2 epa_forecast         6631    0.855         190    0.368    0.340    0.310
    3    smokecast         5576    0.896         118    0.407    0.478    0.296
    3 epa_forecast         5576    0.885         118    0.110    0.316    0.105