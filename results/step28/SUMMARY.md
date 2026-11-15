# Step 28 summary

| ID | result | verdict |
|---|---|---|
| C1 | 14/14 (need 11) | PASS |
| C2 | 14/14 (need 11) | PASS |
| C4 | 12/14 (need 11) | PASS |
| C3 | flags 0/14 (max 2) | PASS |

## Reported (no verdict)

```
{
 "cm01": {
  "n": 14,
  "median_R_flow_me3": 0.5359366601339237,
  "wins_R_flow_me3": 14,
  "median_R_flow_me_local": 0.09670565484936315,
  "wins_R_flow_me_local": 14,
  "median_R_given_me3": 1.297210591173071,
  "wins_R_given_me3": 2,
  "median_R_given_me_local": 0.37017868595813685,
  "wins_R_given_me_local": 14,
  "median_R_enl_me3": 0.5359366601339237,
  "wins_R_enl_me3": 14,
  "median_R_enl_me_local": 0.09670565484936315,
  "wins_R_enl_me_local": 14,
  "flags": 14,
  "missed_alarms": 0,
  "flow_beats_given": 14,
  "pinned_given": 1,
  "pinned_enl": 0,
  "median_lam_given": 0.956216636621469,
  "ratio_given_range": [
   0.7553848437550993,
   4.915088867311321
  ],
  "ratio_enl_range": [
   0.3300561765526041,
   0.6153093599270899
  ]
 },
 "cf01": {
  "n": 14,
  "median_R_flow_me3": 0.5268953270153447,
  "wins_R_flow_me3": 14,
  "median_R_flow_me_local": 0.15835911740401754,
  "wins_R_flow_me_local": 14,
  "median_R_given_me3": 0.5268953270153447,
  "wins_R_given_me3": 14,
  "median_R_given_me_local": 0.15835911740401754,
  "wins_R_given_me_local": 14,
  "median_R_enl_me3": 0.5359366601339237,
  "wins_R_enl_me3": 14,
  "median_R_enl_me_local": 0.16780220100732895,
  "wins_R_enl_me_local": 14,
  "flags": 0,
  "missed_alarms": 0,
  "flow_beats_given": 0,
  "pinned_given": 0,
  "pinned_enl": 0,
  "median_lam_given": 0.921865627746312,
  "ratio_given_range": [
   0.36881164399648936,
   0.6379108061044703
  ],
  "ratio_enl_range": [
   0.3300561765526041,
   0.6153093599270899
  ]
 },
 "cm02": {
  "n": 14,
  "median_R_flow_me3": 0.7988782507306504,
  "wins_R_flow_me3": 12,
  "median_R_flow_me_local": 0.22048592667149988,
  "wins_R_flow_me_local": 14,
  "median_R_given_me3": 1.1496575271869456,
  "wins_R_given_me3": 3,
  "median_R_given_me_local": 0.30197431722093926,
  "wins_R_given_me_local": 14,
  "median_R_enl_me3": 0.7239005257399319,
  "wins_R_enl_me3": 14,
  "median_R_enl_me_local": 0.15343992724086666,
  "wins_R_enl_me_local": 14,
  "flags": 10,
  "missed_alarms": 2,
  "flow_beats_given": 9,
  "pinned_given": 2,
  "pinned_enl": 2,
  "median_lam_given": 0.9169628197139287,
  "ratio_given_range": [
   0.6270342613360547,
   3.1157810436657205
  ],
  "ratio_enl_range": [
   0.36002733661160513,
   0.587153604747956
  ]
 }
}
```

## Per seed

| cond | seed | ratio_given | flag | R_flow | R_given | R_enl |
|---|---|---|---|---|---|---|
| cm01 | 1040 | 4.92 | True | 0.622 | 3.672 | 0.622 |
| cm01 | 1041 | 1.80 | True | 0.464 | 1.257 | 0.464 |
| cm01 | 1042 | 3.81 | True | 0.843 | 2.245 | 0.843 |
| cm01 | 1043 | 1.25 | True | 0.760 | 0.840 | 0.760 |
| cm01 | 1044 | 2.87 | True | 0.240 | 1.962 | 0.240 |
| cm01 | 1045 | 1.41 | True | 0.888 | 1.657 | 0.888 |
| cm01 | 1046 | 0.80 | True | 0.678 | 0.957 | 0.678 |
| cm01 | 1047 | 1.95 | True | 0.526 | 2.321 | 0.526 |
| cm01 | 1048 | 0.99 | True | 0.415 | 1.287 | 0.415 |
| cm01 | 1049 | 2.53 | True | 0.326 | 3.297 | 0.326 |
| cm01 | 1050 | 1.29 | True | 0.375 | 1.004 | 0.375 |
| cm01 | 1051 | 0.76 | True | 0.640 | 1.267 | 0.640 |
| cm01 | 1052 | 0.98 | True | 0.366 | 1.268 | 0.366 |
| cm01 | 1053 | 0.99 | True | 0.546 | 1.307 | 0.546 |
| cf01 | 1040 | 0.44 | False | 0.583 | 0.583 | 0.622 |
| cf01 | 1041 | 0.49 | False | 0.475 | 0.475 | 0.464 |
| cf01 | 1042 | 0.52 | False | 0.637 | 0.637 | 0.843 |
| cf01 | 1043 | 0.64 | False | 0.588 | 0.588 | 0.760 |
| cf01 | 1044 | 0.40 | False | 0.185 | 0.185 | 0.240 |
| cf01 | 1045 | 0.63 | False | 0.956 | 0.956 | 0.888 |
| cf01 | 1046 | 0.51 | False | 0.608 | 0.608 | 0.678 |
| cf01 | 1047 | 0.42 | False | 0.614 | 0.614 | 0.526 |
| cf01 | 1048 | 0.37 | False | 0.391 | 0.391 | 0.415 |
| cf01 | 1049 | 0.38 | False | 0.308 | 0.308 | 0.326 |
| cf01 | 1050 | 0.63 | False | 0.381 | 0.381 | 0.375 |
| cf01 | 1051 | 0.37 | False | 0.573 | 0.573 | 0.640 |
| cf01 | 1052 | 0.40 | False | 0.249 | 0.249 | 0.366 |
| cf01 | 1053 | 0.41 | False | 0.481 | 0.481 | 0.546 |
| cm02 | 1040 | 3.12 | True | 0.982 | 2.472 | 0.982 |
| cm02 | 1041 | 1.45 | True | 0.620 | 1.104 | 0.620 |
| cm02 | 1042 | 2.95 | True | 0.782 | 1.890 | 0.782 |
| cm02 | 1043 | 0.85 | True | 0.855 | 0.637 | 0.855 |
| cm02 | 1044 | 1.75 | True | 0.402 | 1.142 | 0.402 |
| cm02 | 1045 | 1.16 | True | 0.830 | 1.352 | 0.830 |
| cm02 | 1046 | 0.71 | False | 1.157 | 1.157 | 0.733 |
| cm02 | 1047 | 1.21 | True | 0.715 | 1.958 | 0.715 |
| cm02 | 1048 | 0.83 | True | 0.816 | 1.123 | 0.816 |
| cm02 | 1049 | 1.51 | True | 0.639 | 1.995 | 0.639 |
| cm02 | 1050 | 0.95 | True | 0.675 | 1.040 | 0.675 |
| cm02 | 1051 | 0.64 | False | 0.856 | 0.856 | 0.695 |
| cm02 | 1052 | 0.66 | False | 0.765 | 0.765 | 0.323 |
| cm02 | 1053 | 0.63 | False | 1.208 | 1.208 | 0.791 |
