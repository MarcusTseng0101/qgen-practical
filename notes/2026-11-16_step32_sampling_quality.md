# Step 32 (exploration): does the moment win carry over to sampling quality?

Exploration only. It reuses the spent test seeds of steps 23, 26 and 29, so it gives no verdict.
Code: worktree commit a73c98c, `explore/step32_dist/` (`dist.py` refits and saves q; `metrics.py` scores).

## Question
The paper scores only the order-4 to order-6 parity moments (G). Does a model that predicts those well also
sample well, i.e. is its whole distribution q close to the target p?

## Method
- Literature: large-n work (Recio-Armengol et al. 2503.02934) scores samples by test-set MMD plus KGEL.
  On bit strings the Gaussian-kernel MMD^2 equals sum_k C(n,k) a^(n-k) b^k E_k, a weighted sum of the
  per-order parity errors E_k. G is the k = 4..6 slice of it.
- At n = 16 p is known exactly, so every metric is exact: TVD, KL(p||q), classical fidelity,
  E_k for k = 1..16 (Walsh transform), G_hi = mean E_7..E_16, MMD^2 at bandwidths 0.5, 1, 2.
- Refits reproduce the registered G to 1e-15 for all 42 instances.

## Results (wins out of 14 against MaxEnt(3); median ratio model/ME3; MaxEnt-on-graph lost almost everything)

| metric | ideal (step 23) | 1% gate, FlipIQP (step 26) | coherent eps=0.2, recipe (step 29) |
|---|---|---|---|
| G (orders 4-6) | 14 (0.35) | 13 (0.63) | 10 (0.74) |
| G_hi (orders 7-16) | 14 (0.08) | 10 (0.65) | 12 (0.53) |
| order 1 alone | 5 | 2 | 1 |
| TVD | 14 (0.62) | 13 (0.78) | 12 (0.85) |
| KL | 13 (0.61) | 13 (0.56) | 13 (0.75) |
| fidelity | 13 | 13 | 11 |
| MMD, bandwidth 1 | 14 (0.58) | 14 (0.71) | 12 (0.83) |
| MMD, bandwidth 2 | 9 (0.92) | 7 (1.00) | 1 (1.24) |

Median TVD (model / ME3 / ME-graph): ideal 0.13 / 0.24 / 0.38; g01 0.11 / 0.14 / 0.17; xf02 0.18 / 0.20 / 0.26.

## Reading
1. The moment win does carry over to the whole distribution in all three settings (TVD, KL win 12-14 of 14).
2. Orders 7-16, never scored in the paper, are won too; strongly when ideal, weakly under noise.
3. The coherent case looks better on the full distribution (TVD 12/14) than on G (10/14). The recipe's
   loss there is concentrated in orders 1 and 4-6.
4. The IQP models are worse than MaxEnt(3) on single-bit marginals. Wide-kernel MMD, which weights low orders,
   therefore ties or loses (1/14 in the coherent case). The advantage lives in multi-bit correlations.
5. Neither model is a faithful sampler at N = 1e4: fidelity 0.94 vs 0.87 (ideal) means a few tens of samples
   separate either model from the truth. The IQP model is closer, not indistinguishable.

## Not done
- Wrong-graph setting (step 27 recipe) not scored for sampling.
- A formal test needs a pre-registration (prereg/ is the user's) and fresh seeds.
