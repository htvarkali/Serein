# Serein backtest (dev) - 2026-11-23 10:42
code version: 7334216 + uncommitted changes
rows: train 130050, val 32300, conf 32300, test 32725; leads [0, 1, 2, 3]
graph: 425 nodes, 4250 edges
features: 65
leave-sites-out: 85 of 425 monitors hidden

## training smokecast (seed 0)
  epoch   0 train 0.1653 val 0.1159 *
  epoch   1 train 0.1422 val 0.1118 *
  epoch   3 train 0.1345 val 0.1069 *
  epoch   4 train 0.1280 val 0.1055 *
  epoch   7 train 0.1235 val 0.1022 *
  epoch  10 train 0.1202 val 0.1024
  epoch  11 train 0.1191 val 0.1012 *
  epoch  13 train 0.1164 val 0.1008 *
  epoch  18 train 0.1132 val 0.0999 *
  epoch  20 train 0.1151 val 0.1006
  epoch  23 train 0.1141 val 0.0992 *
  epoch  30 train 0.1105 val 0.1012
  epoch  36 train 0.1052 val 0.0988 *
  epoch  40 train 0.1037 val 0.1015
  epoch  50 train 0.1019 val 0.1034
  epoch  60 train 0.0984 val 0.1028
  early stop at epoch 66; best val 0.0988

## training smokecast (seed 1)
  epoch   0 train 0.1671 val 0.1176 *
  epoch   1 train 0.1490 val 0.1105 *
  epoch   2 train 0.1371 val 0.1092 *
  epoch   3 train 0.1325 val 0.1067 *
  epoch   4 train 0.1305 val 0.1046 *
  epoch   7 train 0.1234 val 0.1015 *
  epoch   8 train 0.1234 val 0.1014 *
  epoch  10 train 0.1206 val 0.1003 *
  epoch  16 train 0.1156 val 0.0997 *
  epoch  19 train 0.1121 val 0.0995 *
  epoch  20 train 0.1133 val 0.0996
  epoch  23 train 0.1117 val 0.0990 *
  epoch  25 train 0.1103 val 0.0990 *
  epoch  30 train 0.1077 val 0.1007
  epoch  36 train 0.1055 val 0.0986 *
  epoch  40 train 0.1080 val 0.1016
  epoch  48 train 0.1010 val 0.0984 *
  epoch  50 train 0.1006 val 0.1026
  epoch  60 train 0.0975 val 0.1019
  epoch  70 train 0.0955 val 0.1037
  early stop at epoch 78; best val 0.0984

## training smokecast (seed 2)
  epoch   0 train 0.1644 val 0.1168 *
  epoch   1 train 0.1457 val 0.1121 *
  epoch   2 train 0.1367 val 0.1075 *
  epoch   4 train 0.1311 val 0.1069 *
  epoch   5 train 0.1273 val 0.1057 *
  epoch   6 train 0.1267 val 0.1036 *
  epoch   8 train 0.1214 val 0.1012 *
  epoch  10 train 0.1229 val 0.1025
  epoch  12 train 0.1184 val 0.1009 *
  epoch  15 train 0.1173 val 0.0998 *
  epoch  16 train 0.1153 val 0.0997 *
  epoch  19 train 0.1155 val 0.0990 *
  epoch  20 train 0.1148 val 0.1002
  epoch  30 train 0.1074 val 0.1002
  epoch  40 train 0.1041 val 0.0991
  epoch  46 train 0.1021 val 0.0985 *
  epoch  50 train 0.0997 val 0.1013
  epoch  60 train 0.0983 val 0.1006
  epoch  70 train 0.0960 val 0.1014
  early stop at epoch 76; best val 0.0985

## training smokecast (seed 3)
  epoch   0 train 0.1657 val 0.1174 *
  epoch   1 train 0.1418 val 0.1096 *
  epoch   2 train 0.1398 val 0.1076 *
  epoch   4 train 0.1294 val 0.1043 *
  epoch   5 train 0.1261 val 0.1036 *
  epoch   8 train 0.1216 val 0.1018 *
  epoch  10 train 0.1216 val 0.1040
  epoch  12 train 0.1181 val 0.1013 *
  epoch  13 train 0.1178 val 0.1010 *
  epoch  20 train 0.1122 val 0.1000 *
  epoch  30 train 0.1089 val 0.1025
  epoch  34 train 0.1059 val 0.0998 *
  epoch  40 train 0.1043 val 0.1035
  epoch  47 train 0.1012 val 0.0992 *
  epoch  50 train 0.1006 val 0.1020
  epoch  60 train 0.0967 val 0.1044
  epoch  70 train 0.0952 val 0.1025
  early stop at epoch 77; best val 0.0992

## training smokecast (seed 4)
  epoch   0 train 0.1636 val 0.1149 *
  epoch   1 train 0.1423 val 0.1091 *
  epoch   2 train 0.1363 val 0.1085 *
  epoch   3 train 0.1330 val 0.1074 *
  epoch   4 train 0.1288 val 0.1037 *
  epoch   9 train 0.1215 val 0.1030 *
  epoch  10 train 0.1193 val 0.1020 *
  epoch  11 train 0.1193 val 0.1014 *
  epoch  13 train 0.1169 val 0.0990 *
  epoch  20 train 0.1139 val 0.1012
  epoch  28 train 0.1110 val 0.0984 *
  epoch  30 train 0.1076 val 0.1019
  epoch  40 train 0.1050 val 0.0997
  epoch  50 train 0.1008 val 0.1018
  early stop at epoch 58; best val 0.0984

## training smokecast_nograph (seed 0)
  epoch   0 train 0.1751 val 0.1189 *
  epoch   1 train 0.1428 val 0.1130 *
  epoch   2 train 0.1394 val 0.1097 *
  epoch   3 train 0.1355 val 0.1081 *
  epoch   4 train 0.1311 val 0.1064 *
  epoch   5 train 0.1293 val 0.1052 *
  epoch   6 train 0.1320 val 0.1045 *
  epoch   7 train 0.1274 val 0.1028 *
  epoch  10 train 0.1242 val 0.1024 *
  epoch  13 train 0.1222 val 0.1015 *
  epoch  16 train 0.1216 val 0.1012 *
  epoch  18 train 0.1202 val 0.1003 *
  epoch  20 train 0.1212 val 0.1019
  epoch  23 train 0.1219 val 0.0996 *
  epoch  30 train 0.1174 val 0.1003
  epoch  40 train 0.1156 val 0.1008
  epoch  46 train 0.1141 val 0.0993 *
  epoch  50 train 0.1147 val 0.1011
  epoch  60 train 0.1138 val 0.1006
  epoch  70 train 0.1116 val 0.1004
  early stop at epoch 76; best val 0.0993

## training smokecast_nograph (seed 1)
  epoch   0 train 0.1747 val 0.1225 *
  epoch   1 train 0.1507 val 0.1129 *
  epoch   2 train 0.1377 val 0.1075 *
  epoch   3 train 0.1354 val 0.1073 *
  epoch   4 train 0.1330 val 0.1064 *
  epoch   5 train 0.1315 val 0.1049 *
  epoch   6 train 0.1298 val 0.1046 *
  epoch   7 train 0.1272 val 0.1024 *
  epoch   8 train 0.1284 val 0.1021 *
  epoch   9 train 0.1251 val 0.1018 *
  epoch  10 train 0.1248 val 0.1016 *
  epoch  14 train 0.1220 val 0.1013 *
  epoch  20 train 0.1215 val 0.1006 *
  epoch  23 train 0.1219 val 0.0998 *
  epoch  27 train 0.1189 val 0.0995 *
  epoch  30 train 0.1189 val 0.1009
  epoch  40 train 0.1205 val 0.0998
  epoch  50 train 0.1141 val 0.0996
  epoch  55 train 0.1130 val 0.0994 *
  epoch  56 train 0.1133 val 0.0987 *
  epoch  60 train 0.1136 val 0.1007
  epoch  70 train 0.1124 val 0.1023
  epoch  80 train 0.1123 val 0.0998
  early stop at epoch 86; best val 0.0987

## training smokecast_nograph (seed 2)
  epoch   0 train 0.1725 val 0.1202 *
  epoch   1 train 0.1465 val 0.1118 *
  epoch   2 train 0.1377 val 0.1093 *
  epoch   3 train 0.1346 val 0.1068 *
  epoch   4 train 0.1329 val 0.1058 *
  epoch   6 train 0.1306 val 0.1034 *
  epoch   8 train 0.1261 val 0.1026 *
  epoch  10 train 0.1265 val 0.1037
  epoch  12 train 0.1239 val 0.1015 *
  epoch  18 train 0.1247 val 0.1013 *
  epoch  19 train 0.1222 val 0.1009 *
  epoch  20 train 0.1220 val 0.1007 *
  epoch  21 train 0.1201 val 0.1006 *
  epoch  22 train 0.1210 val 0.1003 *
  epoch  30 train 0.1176 val 0.1014
  epoch  35 train 0.1168 val 0.1003 *
  epoch  40 train 0.1168 val 0.1000 *
  epoch  43 train 0.1155 val 0.1000 *
  epoch  45 train 0.1143 val 0.0996 *
  epoch  50 train 0.1133 val 0.1012
  epoch  60 train 0.1122 val 0.1011
  epoch  70 train 0.1111 val 0.1015
  early stop at epoch 75; best val 0.0996

## training smokecast_nograph (seed 3)
  epoch   0 train 0.1753 val 0.1224 *
  epoch   1 train 0.1435 val 0.1120 *
  epoch   2 train 0.1394 val 0.1087 *
  epoch   3 train 0.1365 val 0.1086 *
  epoch   4 train 0.1317 val 0.1055 *
  epoch   5 train 0.1293 val 0.1053 *
  epoch   7 train 0.1286 val 0.1028 *
  epoch   9 train 0.1259 val 0.1027 *
  epoch  10 train 0.1259 val 0.1031
  epoch  11 train 0.1248 val 0.1027 *
  epoch  12 train 0.1239 val 0.1024 *
  epoch  13 train 0.1234 val 0.1015 *
  epoch  14 train 0.1238 val 0.1009 *
  epoch  16 train 0.1212 val 0.1002 *
  epoch  20 train 0.1200 val 0.1006
  epoch  22 train 0.1196 val 0.1000 *
  epoch  27 train 0.1201 val 0.0995 *
  epoch  30 train 0.1188 val 0.1007
  epoch  40 train 0.1152 val 0.0998
  epoch  50 train 0.1137 val 0.0997
  epoch  55 train 0.1131 val 0.0994 *
  epoch  57 train 0.1131 val 0.0991 *
  epoch  59 train 0.1123 val 0.0986 *
  epoch  60 train 0.1124 val 0.1005
  epoch  70 train 0.1122 val 0.1001
  epoch  80 train 0.1101 val 0.1001
  early stop at epoch 89; best val 0.0986

## training smokecast_nograph (seed 4)
  epoch   0 train 0.1735 val 0.1192 *
  epoch   1 train 0.1444 val 0.1097 *
  epoch   2 train 0.1372 val 0.1082 *
  epoch   3 train 0.1343 val 0.1069 *
  epoch   4 train 0.1323 val 0.1043 *
  epoch   7 train 0.1271 val 0.1038 *
  epoch   9 train 0.1251 val 0.1035 *
  epoch  10 train 0.1250 val 0.1029 *
  epoch  11 train 0.1249 val 0.1023 *
  epoch  15 train 0.1233 val 0.1021 *
  epoch  16 train 0.1219 val 0.1010 *
  epoch  18 train 0.1219 val 0.1010 *
  epoch  20 train 0.1209 val 0.1004 *
  epoch  27 train 0.1200 val 0.1001 *
  epoch  30 train 0.1173 val 0.1024
  epoch  31 train 0.1179 val 0.1000 *
  epoch  40 train 0.1163 val 0.1004
  epoch  42 train 0.1161 val 0.1000 *
  epoch  45 train 0.1151 val 0.0993 *
  epoch  50 train 0.1136 val 0.0993
  epoch  59 train 0.1137 val 0.0991 *
  epoch  60 train 0.1136 val 0.1002
  epoch  70 train 0.1113 val 0.1011
  epoch  80 train 0.1109 val 0.1001
  early stop at epoch 89; best val 0.0991
warning cut-offs P(>=35.5) tuned on calibration: {0: 0.4250000000000001, 1: 0.4500000000000001, 2: 0.47500000000000014, 3: 0.4500000000000001}

## Results: all site-days
RMSE (µg/m³, lower is better)
lead                     0      1      2      3
model                                          
aqm_bc               10.14  11.02  12.35    NaN
climatology          13.44  13.76  13.81  13.71
hrrr_smoke           12.63   9.05    NaN    NaN
noaa_best            10.14  11.02  12.35  15.48
persistence          10.15  13.79  14.97  15.48
persistence_morning   7.38  14.89    NaN    NaN
smokecast             5.04   7.86   9.58  11.37
smokecast_nograph     5.51   8.18  10.17  12.45

RMSE on smoke-affected days (HMS plume overhead yesterday)
lead                     0      1      2      3
model                                          
aqm_bc               14.77  15.87  17.50    NaN
climatology          19.95  20.12  19.77  19.70
hrrr_smoke           18.75  12.73    NaN    NaN
noaa_best            14.77  15.87  17.50  22.55
persistence          15.03  20.29  21.66  22.55
persistence_morning  10.36  21.51    NaN    NaN
smokecast             7.32  11.12  13.60  16.37
smokecast_nograph     8.06  11.67  14.53  18.02

RMSE at HIDDEN monitors (no readings; persistence/climatology use data a real unmonitored place would not have)
lead                     0      1      2      3
model                                          
aqm_bc               10.46  11.14  11.93    NaN
climatology          12.66  12.66  12.25  11.90
hrrr_smoke            9.12  10.10    NaN    NaN
noaa_best            10.46  11.14  11.93  14.10
persistence          10.00  13.45  13.46  14.10
persistence_morning   6.78  15.04    NaN    NaN
smokecast             6.92   8.39   9.90  11.38
smokecast_nograph     8.47   8.90  10.52  13.76

USG+ critical success index (higher is better)
lead                     0      1      2      3
model                                          
aqm_bc               0.369  0.285  0.142    NaN
climatology          0.000  0.000  0.000  0.000
hrrr_smoke           0.509  0.468    NaN    NaN
noaa_best            0.369  0.285  0.142  0.151
persistence          0.376  0.257  0.179  0.151
persistence_morning  0.501  0.251    NaN    NaN
smokecast            0.632  0.516  0.445  0.313
smokecast_nograph    0.660  0.533  0.407  0.273
smokecast_warnrule   0.631  0.505  0.435  0.307

90% interval coverage (target 0.90)
lead                   0      1      2      3
model                                        
smokecast          0.898  0.893  0.900  0.904
smokecast_nograph  0.898  0.893  0.905  0.911

Head-to-head (same rows; skill = 1 - RMSE_smokecast/RMSE_baseline; CI = 95% day-bootstrap of RMSE diff)
 lead                  vs     n  rmse_smokecast  rmse_baseline  skill   ci_lo  ci_hi
    0           noaa_best 25030           5.037         10.138  0.503  -7.358 -2.921
    0              aqm_bc 25030           5.037         10.138  0.503  -7.358 -2.921
    0          hrrr_smoke 25030           5.037         12.630  0.601 -12.336 -3.392
    0         persistence 24732           5.054         10.149  0.502  -7.715 -2.268
    0 persistence_morning 25030           5.037          7.378  0.317  -2.962 -1.661
    0   smokecast_nograph 25030           5.037          5.510  0.086  -0.902 -0.133
    1           noaa_best 25041           7.858         11.022  0.287  -4.564 -1.584
    1              aqm_bc 25041           7.858         11.022  0.287  -4.564 -1.584
    1          hrrr_smoke 25041           7.858          9.053  0.132  -2.101 -0.381
    1         persistence 24562           7.825         13.795  0.433  -9.010 -2.789
    1 persistence_morning 24897           7.868         14.892  0.472  -9.544 -4.376
    1   smokecast_nograph 25041           7.858          8.183  0.040  -0.574 -0.044
    2           noaa_best 24730           9.577         12.348  0.224  -4.077 -1.533
    2              aqm_bc 24730           9.577         12.348  0.224  -4.077 -1.533
    2         persistence 24144           9.375         14.965  0.374  -7.961 -3.203
    2   smokecast_nograph 24730           9.577         10.175  0.059  -1.166 -0.182
    3           noaa_best 23787          11.211         15.475  0.276  -7.039 -1.935
    3         persistence 23787          11.211         15.475  0.276  -7.039 -1.935
    3   smokecast_nograph 24432          11.374         12.450  0.086  -1.999 -0.366

vs. official EPA AQI forecast (reporting areas, category scores)
 lead          who  n_area_days  cat_acc  usg_events  usg_pod  usg_far  usg_csi
    0    smokecast        10948    0.916         224    0.799    0.211    0.658
    0 epa_forecast        10948    0.842         224    0.665    0.402    0.460
    1    smokecast        10775    0.881         244    0.697    0.351    0.506
    1 epa_forecast        10775    0.827         244    0.459    0.467    0.327
    2    smokecast         6631    0.896         190    0.642    0.299    0.504
    2 epa_forecast         6631    0.855         190    0.368    0.340    0.310
    3    smokecast         5576    0.895         118    0.415    0.479    0.301
    3 epa_forecast         5576    0.885         118    0.110    0.316    0.105