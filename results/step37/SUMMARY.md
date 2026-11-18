# Step 37 summary

| ID | result | verdict |
|---|---|---|
| A1 | 13/14 (need 11) | PASS |
| A2 | 13/14 (need 12) | PASS |
| A3 | 28/28 (need 26) | PASS |
| A4 | 28/28 (need 24) | PASS |
| A5 | 26/28 (need 23) | PASS |

## Reported (no verdict)

```
{
 "cf_full": {
  "n": 14,
  "n_with_recipe": 14,
  "median_R_recipe": 0.4157210776628898,
  "median_R_flip_given": 0.5563171184587925,
  "recipe_beats_flip_given": 10,
  "picked": {
   "full/coh": 12,
   "full/flip": 2
  },
  "drop_near_threshold": {},
  "gate_ratio_near_threshold": {
   "1231": 0.9792837275767284,
   "1239": 1.2291964356841485,
   "1240": 0.9729416125345896,
   "1243": 1.2271085447477201
  }
 },
 "cf_miss": {
  "n": 14,
  "n_with_recipe": 14,
  "median_R_recipe": 0.48363475352161156,
  "median_R_flip_given": 2.0224118092893875,
  "recipe_beats_flip_given": 14,
  "picked": {
   "enl/coh": 11,
   "enl/flip": 3
  },
  "drop_near_threshold": {},
  "gate_ratio_near_threshold": {
   "1239": 1.031955707447907,
   "1240": 0.8347111334105575,
   "1243": 0.9782299092481115
  }
 },
 "pf_full": {
  "n": 14,
  "n_with_recipe": 14,
  "median_R_recipe": 0.20123816473213985,
  "median_R_flip_given": 0.20123816473213985,
  "recipe_beats_flip_given": 1,
  "picked": {
   "full/coh": 2,
   "full/flip": 12
  },
  "drop_near_threshold": {
   "1232": 1.6881097101578095
  },
  "gate_ratio_near_threshold": {
   "1233": 0.8788725396091983,
   "1234": 1.0957867822175447
  }
 },
 "pf_miss": {
  "n": 14,
  "n_with_recipe": 14,
  "median_R_recipe": 0.23693829190418375,
  "median_R_flip_given": 1.7258845421638593,
  "recipe_beats_flip_given": 14,
  "picked": {
   "enl/flip": 14
  },
  "drop_near_threshold": {},
  "gate_ratio_near_threshold": {
   "1230": 0.8945235336657268,
   "1234": 0.9173583887360403,
   "1241": 0.9765725252060776
  }
 },
 "coh": {
  "n_needed": 25,
  "n_done": 25,
  "restarts_at_maxiter": 124,
  "eps_at_bound": 34
 }
}
```

## Per seed (R = G / G_me3)

| cond | given | seed | drop | graph* | gate ratio | pick | R_recipe | R_flip_given |
|---|---|---|---|---|---|---|---|---|
| cf | full | 1230 | 1.42 | full | 2.34 | coh | 0.751 | 0.654 |
| cf | full | 1231 | 1.28 | full | 0.98 | flip | 0.201 | 0.201 |
| cf | full | 1232 | 1.47 | full | 3.09 | coh | 0.186 | 0.500 |
| cf | full | 1233 | 1.33 | full | 2.10 | coh | 0.376 | 0.442 |
| cf | full | 1234 | 1.35 | full | 3.26 | coh | 0.897 | 1.328 |
| cf | full | 1235 | 1.22 | full | 2.74 | coh | 0.362 | 0.369 |
| cf | full | 1236 | 1.32 | full | 1.80 | coh | 0.569 | 1.202 |
| cf | full | 1237 | 1.26 | full | 2.94 | coh | 0.312 | 0.507 |
| cf | full | 1238 | 1.47 | full | 3.79 | coh | 0.724 | 1.330 |
| cf | full | 1239 | 1.19 | full | 1.23 | coh | 0.470 | 0.606 |
| cf | full | 1240 | 1.17 | full | 0.97 | flip | 0.234 | 0.234 |
| cf | full | 1241 | 1.28 | full | 2.78 | coh | 0.326 | 0.891 |
| cf | full | 1242 | 1.19 | full | 2.64 | coh | 0.456 | 0.617 |
| cf | full | 1243 | 1.25 | full | 1.23 | coh | 1.074 | 0.435 |
| cf | miss | 1230 | 4.86 | enl | 1.64 | coh | 0.328 | 2.277 |
| cf | miss | 1231 | 6.60 | enl | 0.76 | flip | 0.216 | 0.582 |
| cf | miss | 1232 | 3.74 | enl | 2.10 | coh | 0.476 | 1.193 |
| cf | miss | 1233 | 18.78 | enl | 1.58 | coh | 0.639 | 1.764 |
| cf | miss | 1234 | 25.00 | enl | 2.41 | coh | 1.358 | 5.292 |
| cf | miss | 1235 | 9.93 | enl | 2.25 | coh | 0.284 | 1.680 |
| cf | miss | 1236 | 5.64 | enl | 1.36 | coh | 0.919 | 3.446 |
| cf | miss | 1237 | 17.49 | enl | 2.33 | coh | 0.328 | 3.960 |
| cf | miss | 1238 | 5.03 | enl | 2.58 | coh | 0.872 | 2.622 |
| cf | miss | 1239 | 8.56 | enl | 1.03 | coh | 0.492 | 2.046 |
| cf | miss | 1240 | 7.23 | enl | 0.83 | flip | 0.258 | 1.931 |
| cf | miss | 1241 | 4.13 | enl | 2.16 | coh | 0.593 | 1.324 |
| cf | miss | 1242 | 9.60 | enl | 2.21 | coh | 0.431 | 1.999 |
| cf | miss | 1243 | 45.83 | enl | 0.98 | flip | 0.515 | 7.884 |
| pf | full | 1230 | 0.54 | full | 0.49 | flip | 0.092 | 0.092 |
| pf | full | 1231 | 1.17 | full | 0.62 | flip | 0.148 | 0.148 |
| pf | full | 1232 | 1.69 | full | 0.78 | flip | 0.180 | 0.180 |
| pf | full | 1233 | 1.39 | full | 0.88 | flip | 0.238 | 0.238 |
| pf | full | 1234 | 1.19 | full | 1.10 | coh | 1.144 | 1.049 |
| pf | full | 1235 | 0.86 | full | 0.58 | flip | 0.091 | 0.091 |
| pf | full | 1236 | 1.07 | full | 0.56 | flip | 0.200 | 0.200 |
| pf | full | 1237 | 1.31 | full | 0.67 | flip | 0.203 | 0.203 |
| pf | full | 1238 | 1.23 | full | 0.67 | flip | 0.253 | 0.253 |
| pf | full | 1239 | 1.09 | full | 0.49 | flip | 0.290 | 0.290 |
| pf | full | 1240 | 1.02 | full | 0.58 | flip | 0.135 | 0.135 |
| pf | full | 1241 | 1.47 | full | 1.44 | coh | 0.513 | 0.620 |
| pf | full | 1242 | 1.05 | full | 0.61 | flip | 0.107 | 0.107 |
| pf | full | 1243 | 1.20 | full | 0.67 | flip | 0.584 | 0.584 |
| pf | miss | 1230 | 5.77 | enl | 0.89 | flip | 1.027 | 2.449 |
| pf | miss | 1231 | 6.49 | enl | 0.53 | flip | 0.149 | 0.461 |
| pf | miss | 1232 | 9.39 | enl | 0.46 | flip | 0.083 | 1.349 |
| pf | miss | 1233 | 30.14 | enl | 0.63 | flip | 0.107 | 1.561 |
| pf | miss | 1234 | 35.38 | enl | 0.92 | flip | 0.901 | 4.125 |
| pf | miss | 1235 | 15.53 | enl | 0.68 | flip | 0.279 | 2.342 |
| pf | miss | 1236 | 4.98 | enl | 0.52 | flip | 0.479 | 1.210 |
| pf | miss | 1237 | 17.72 | enl | 0.51 | flip | 0.119 | 2.279 |
| pf | miss | 1238 | 10.15 | enl | 0.55 | flip | 0.165 | 1.890 |
| pf | miss | 1239 | 11.66 | enl | 0.45 | flip | 0.260 | 2.133 |
| pf | miss | 1240 | 5.97 | enl | 0.57 | flip | 0.196 | 1.215 |
| pf | miss | 1241 | 5.28 | enl | 0.98 | flip | 0.412 | 1.158 |
| pf | miss | 1242 | 10.81 | enl | 0.58 | flip | 0.214 | 1.471 |
| pf | miss | 1243 | 41.48 | enl | 0.56 | flip | 0.487 | 10.412 |
