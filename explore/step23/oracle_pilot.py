"""Diagnostic only: oracle generator support (true target gens). Ceiling for any sparse IQP."""
import sys, time, numpy as np
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.bits import masks_up_to, popcount
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import sample_indices
from src.step1.walsh import empirical_distribution, parity_coefficients
from src.step4.targets import iqp4_target
from src.step14.run import SIGMA
n=16; ops=masks_up_to(n,3)
seed=int(sys.argv[1]); N=int(sys.argv[2]); mode=sys.argv[3]
p,masks,_,_=iqp4_target(SIGMA,seed,n)
fh=parity_coefficients(empirical_distribution(sample_indices(p,N,seed),n))[ops]
me=MaxEntModel(n,3); qme=me.prob(me.fit_moments(fh,ops).params)
gens = masks if mode=="all" else masks[popcount(masks)<=3]
t=time.time(); m=IQPModel(n,gens=gens); f=m.fit_moments(fh,ops,seed=seed,n_restarts=3)
q=m.prob(f.params)
Gme=M1.completion_gap(qme,p,n)["G"]; Gq=M1.completion_gap(q,p,n)["G"]
print(f"seed {seed} N {N} oracle-{mode} k={len(gens)}  R={Gq/Gme:.3f}  resid={f.train_residual:.2e}  {time.time()-t:.0f}s", flush=True)
