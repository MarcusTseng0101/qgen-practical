# Step 27 summary

| ID | result | verdict |
|---|---|---|
| K1 | 12/14 (need 11) | PASS |
| K2 | 13/14 (need 11) | PASS |
| K4 | 13/14 (need 11) | PASS |
| K3 | flags 1/14 (max 2) | PASS |

## Reported (no verdict)

```
{
 "mg01": {
  "n": 14,
  "median_R_flow_me3": 0.6642606703616654,
  "wins_R_flow_me3": 12,
  "median_R_flow_me_local": 0.16382924875897653,
  "wins_R_flow_me_local": 14,
  "median_R_given_me3": 1.1081052810726382,
  "wins_R_given_me3": 6,
  "median_R_given_me_local": 0.20278472608838433,
  "wins_R_given_me_local": 14,
  "median_R_enl_me3": 0.7132785176227158,
  "wins_R_enl_me3": 12,
  "median_R_enl_me_local": 0.17220985974202174,
  "wins_R_enl_me_local": 14,
  "flags": 8,
  "missed_alarms": 1,
  "flow_beats_given": 7,
  "pinned_given": 1,
  "pinned_enl": 3,
  "median_lam_given": 0.9252641299344992,
  "ratio_given_range": [
   0.5654663422565126,
   2.368485768997866
  ],
  "ratio_enl_range": [
   0.265922889930929,
   0.714391471375156
  ]
 },
 "fg01": {
  "n": 14,
  "median_R_flow_me3": 0.5695346202105998,
  "wins_R_flow_me3": 13,
  "median_R_flow_me_local": 0.2024919395388226,
  "wins_R_flow_me_local": 14,
  "median_R_given_me3": 0.5695346202105998,
  "wins_R_given_me3": 13,
  "median_R_given_me_local": 0.2024919395388226,
  "wins_R_given_me_local": 14,
  "median_R_enl_me3": 0.7132785176227158,
  "wins_R_enl_me3": 12,
  "median_R_enl_me_local": 0.2506028064161902,
  "wins_R_enl_me_local": 14,
  "flags": 1,
  "missed_alarms": 1,
  "flow_beats_given": 0,
  "pinned_given": 0,
  "pinned_enl": 3,
  "median_lam_given": 0.9102244393218178,
  "ratio_given_range": [
   0.28797606873829695,
   0.7697885444101078
  ],
  "ratio_enl_range": [
   0.265922889930929,
   0.714391471375156
  ]
 },
 "mg005": {
  "n": 14,
  "median_R_flow_me3": 0.5603472967520279,
  "wins_R_flow_me3": 13,
  "median_R_flow_me_local": 0.13414701906260212,
  "wins_R_flow_me_local": 14,
  "median_R_given_me3": 1.2621161885310208,
  "wins_R_given_me3": 4,
  "median_R_given_me_local": 0.20341919699853328,
  "wins_R_given_me_local": 14,
  "median_R_enl_me3": 0.5537626668393965,
  "wins_R_enl_me3": 13,
  "median_R_enl_me_local": 0.12019763469151801,
  "wins_R_enl_me_local": 14,
  "flags": 12,
  "missed_alarms": 0,
  "flow_beats_given": 12,
  "pinned_given": 0,
  "pinned_enl": 1,
  "median_lam_given": 0.9679739324127072,
  "ratio_given_range": [
   0.48022109676188657,
   3.8606621768002882
  ],
  "ratio_enl_range": [
   0.3094895231796237,
   0.6764828789389922
  ]
 }
}
```

## Per seed

| cond | seed | ratio_given | flag | R_flow | R_given | R_enl |
|---|---|---|---|---|---|---|
| mg01 | 1020 | 1.14 | True | 0.720 | 1.204 | 0.720 |
| mg01 | 1021 | 2.37 | True | 0.622 | 1.730 | 0.622 |
| mg01 | 1022 | 1.23 | True | 0.471 | 1.245 | 0.471 |
| mg01 | 1023 | 0.62 | False | 0.939 | 0.939 | 0.782 |
| mg01 | 1024 | 0.98 | True | 1.121 | 1.667 | 1.121 |
| mg01 | 1025 | 0.81 | True | 0.611 | 0.610 | 0.611 |
| mg01 | 1026 | 0.92 | True | 0.599 | 1.287 | 0.599 |
| mg01 | 1027 | 1.10 | True | 0.707 | 1.361 | 0.707 |
| mg01 | 1028 | 0.71 | False | 0.865 | 0.865 | 1.095 |
| mg01 | 1029 | 0.67 | False | 0.501 | 0.501 | 0.461 |
| mg01 | 1030 | 0.57 | False | 0.330 | 0.330 | 0.801 |
| mg01 | 1031 | 0.61 | False | 0.527 | 0.527 | 0.654 |
| mg01 | 1032 | 0.65 | False | 1.012 | 1.012 | 0.771 |
| mg01 | 1033 | 1.06 | True | 0.890 | 1.437 | 0.890 |
| fg01 | 1020 | 0.77 | True | 0.720 | 0.593 | 0.720 |
| fg01 | 1021 | 0.48 | False | 0.566 | 0.566 | 0.622 |
| fg01 | 1022 | 0.42 | False | 0.399 | 0.399 | 0.471 |
| fg01 | 1023 | 0.45 | False | 0.535 | 0.535 | 0.782 |
| fg01 | 1024 | 0.56 | False | 1.074 | 1.074 | 1.121 |
| fg01 | 1025 | 0.60 | False | 0.604 | 0.604 | 0.611 |
| fg01 | 1026 | 0.29 | False | 0.543 | 0.543 | 0.599 |
| fg01 | 1027 | 0.51 | False | 0.649 | 0.649 | 0.707 |
| fg01 | 1028 | 0.52 | False | 0.599 | 0.599 | 1.095 |
| fg01 | 1029 | 0.48 | False | 0.364 | 0.364 | 0.461 |
| fg01 | 1030 | 0.53 | False | 0.409 | 0.409 | 0.801 |
| fg01 | 1031 | 0.52 | False | 0.670 | 0.670 | 0.654 |
| fg01 | 1032 | 0.39 | False | 0.522 | 0.522 | 0.771 |
| fg01 | 1033 | 0.52 | False | 0.573 | 0.573 | 0.890 |
| mg005 | 1020 | 1.25 | True | 0.601 | 1.089 | 0.601 |
| mg005 | 1021 | 3.86 | True | 0.485 | 2.682 | 0.485 |
| mg005 | 1022 | 2.64 | True | 0.357 | 2.520 | 0.357 |
| mg005 | 1023 | 0.77 | True | 0.511 | 1.011 | 0.511 |
| mg005 | 1024 | 1.23 | True | 0.905 | 1.707 | 0.905 |
| mg005 | 1025 | 0.85 | True | 0.700 | 0.746 | 0.700 |
| mg005 | 1026 | 1.35 | True | 0.516 | 1.876 | 0.516 |
| mg005 | 1027 | 1.38 | True | 0.906 | 1.788 | 0.906 |
| mg005 | 1028 | 0.97 | True | 1.014 | 1.262 | 1.014 |
| mg005 | 1029 | 0.67 | False | 0.552 | 0.552 | 0.356 |
| mg005 | 1030 | 0.48 | False | 0.458 | 0.458 | 0.505 |
| mg005 | 1031 | 0.76 | True | 0.569 | 0.794 | 0.569 |
| mg005 | 1032 | 0.78 | True | 0.538 | 1.263 | 0.538 |
| mg005 | 1033 | 1.06 | True | 0.705 | 1.357 | 0.705 |
