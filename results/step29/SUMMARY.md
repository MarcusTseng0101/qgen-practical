# Step 29 summary

| ID | result | verdict |
|---|---|---|
| X1 | 12/14 (need 11) | PASS |
| X2 | 10/14 (need 11) | FAIL |
| X4 | 13/14 (need 11) | PASS |
| X3 | flags 3/14 (max 2) | FAIL |

## Reported (no verdict)

```
{
 "xm02": {
  "n": 14,
  "median_R_flow_me3": 0.68201925064866,
  "wins_R_flow_me3": 12,
  "median_R_flow_me_local": 0.1214163208595733,
  "wins_R_flow_me_local": 14,
  "median_R_given_me3": 1.1943388302162243,
  "wins_R_given_me3": 4,
  "median_R_given_me_local": 0.3461718460170903,
  "wins_R_given_me_local": 14,
  "median_R_enl_me3": 0.6873595589945936,
  "wins_R_enl_me3": 12,
  "median_R_enl_me_local": 0.1214163208595733,
  "wins_R_enl_me_local": 14,
  "flags": 13,
  "missed_alarms": 0,
  "flow_beats_given": 13,
  "pinned_given": 2,
  "pinned_enl": 1,
  "median_lam_given": 1.0,
  "ratio_given_range": [
   0.609079015279616,
   3.3547279550329887
  ],
  "ratio_enl_range": [
   0.2227797556386141,
   0.8225236127656365
  ]
 },
 "xf02": {
  "n": 14,
  "median_R_flow_me3": 0.7376657870383585,
  "wins_R_flow_me3": 10,
  "median_R_flow_me_local": 0.3174134181775484,
  "wins_R_flow_me_local": 14,
  "median_R_given_me3": 0.6994737704708176,
  "wins_R_given_me3": 10,
  "median_R_given_me_local": 0.2680884625422786,
  "wins_R_given_me_local": 14,
  "median_R_enl_me3": 0.6873595589945936,
  "wins_R_enl_me3": 12,
  "median_R_enl_me_local": 0.23580788638507327,
  "wins_R_enl_me_local": 14,
  "flags": 3,
  "missed_alarms": 3,
  "flow_beats_given": 2,
  "pinned_given": 1,
  "pinned_enl": 1,
  "median_lam_given": 0.9853357715503512,
  "ratio_given_range": [
   0.3456589888401929,
   1.0266113876290677
  ],
  "ratio_enl_range": [
   0.2227797556386141,
   0.8225236127656365
  ]
 },
 "xm01": {
  "n": 14,
  "median_R_flow_me3": 0.6606937860500331,
  "wins_R_flow_me3": 13,
  "median_R_flow_me_local": 0.12905707659199428,
  "wins_R_flow_me_local": 14,
  "median_R_given_me3": 1.0914252185852231,
  "wins_R_given_me3": 6,
  "median_R_given_me_local": 0.2601598191358823,
  "wins_R_given_me_local": 14,
  "median_R_enl_me3": 0.6881333424823368,
  "wins_R_enl_me3": 14,
  "median_R_enl_me_local": 0.12905707659199428,
  "wins_R_enl_me_local": 14,
  "flags": 11,
  "missed_alarms": 1,
  "flow_beats_given": 9,
  "pinned_given": 1,
  "pinned_enl": 1,
  "median_lam_given": 0.995788281224153,
  "ratio_given_range": [
   0.5805132035274286,
   3.219182580437066
  ],
  "ratio_enl_range": [
   0.2246657140855849,
   0.6876486008439793
  ]
 }
}
```

## Per seed

| cond | seed | ratio_given | flag | R_flow | R_given | R_enl |
|---|---|---|---|---|---|---|
| xm02 | 1060 | 1.80 | True | 0.493 | 1.061 | 0.493 |
| xm02 | 1061 | 3.24 | True | 0.813 | 2.304 | 0.813 |
| xm02 | 1062 | 3.35 | True | 0.489 | 2.453 | 0.489 |
| xm02 | 1063 | 0.61 | False | 0.543 | 0.543 | 0.621 |
| xm02 | 1064 | 0.82 | True | 0.902 | 1.456 | 0.902 |
| xm02 | 1065 | 2.16 | True | 0.773 | 2.369 | 0.773 |
| xm02 | 1066 | 0.90 | True | 1.229 | 1.233 | 1.229 |
| xm02 | 1067 | 3.02 | True | 0.930 | 3.685 | 0.930 |
| xm02 | 1068 | 0.89 | True | 0.383 | 0.658 | 0.383 |
| xm02 | 1069 | 1.87 | True | 0.599 | 1.644 | 0.599 |
| xm02 | 1070 | 1.02 | True | 1.083 | 1.156 | 1.083 |
| xm02 | 1071 | 0.96 | True | 0.543 | 0.927 | 0.543 |
| xm02 | 1072 | 1.13 | True | 0.610 | 1.076 | 0.610 |
| xm02 | 1073 | 0.89 | True | 0.754 | 0.812 | 0.754 |
| xf02 | 1060 | 1.03 | True | 0.493 | 0.580 | 0.493 |
| xf02 | 1061 | 0.71 | False | 0.678 | 0.678 | 0.813 |
| xf02 | 1062 | 0.73 | False | 0.468 | 0.468 | 0.489 |
| xf02 | 1063 | 0.57 | False | 0.474 | 0.474 | 0.621 |
| xf02 | 1064 | 0.67 | False | 1.430 | 1.430 | 0.902 |
| xf02 | 1065 | 0.76 | True | 0.773 | 0.500 | 0.773 |
| xf02 | 1066 | 0.74 | False | 1.074 | 1.074 | 1.229 |
| xf02 | 1067 | 0.35 | False | 1.207 | 1.207 | 0.930 |
| xf02 | 1068 | 0.70 | False | 0.408 | 0.408 | 0.383 |
| xf02 | 1069 | 0.52 | False | 0.934 | 0.934 | 0.599 |
| xf02 | 1070 | 0.80 | True | 1.083 | 1.188 | 1.083 |
| xf02 | 1071 | 0.67 | False | 0.721 | 0.721 | 0.543 |
| xf02 | 1072 | 0.60 | False | 0.610 | 0.610 | 0.610 |
| xf02 | 1073 | 0.72 | False | 0.755 | 0.755 | 0.754 |
| xm01 | 1060 | 0.98 | True | 0.579 | 0.677 | 0.579 |
| xm01 | 1061 | 2.82 | True | 0.979 | 1.853 | 0.979 |
| xm01 | 1062 | 3.21 | True | 0.368 | 1.596 | 0.368 |
| xm01 | 1063 | 0.63 | False | 0.664 | 0.664 | 0.746 |
| xm01 | 1064 | 0.68 | False | 1.119 | 1.119 | 0.863 |
| xm01 | 1065 | 2.62 | True | 0.657 | 2.665 | 0.657 |
| xm01 | 1066 | 0.76 | True | 0.862 | 0.839 | 0.862 |
| xm01 | 1067 | 3.22 | True | 0.719 | 4.207 | 0.719 |
| xm01 | 1068 | 0.58 | False | 0.388 | 0.388 | 0.291 |
| xm01 | 1069 | 1.95 | True | 0.428 | 1.459 | 0.428 |
| xm01 | 1070 | 1.27 | True | 0.937 | 1.226 | 0.937 |
| xm01 | 1071 | 0.94 | True | 0.443 | 0.979 | 0.443 |
| xm01 | 1072 | 1.28 | True | 0.536 | 1.064 | 0.536 |
| xm01 | 1073 | 0.79 | True | 0.753 | 0.649 | 0.753 |
