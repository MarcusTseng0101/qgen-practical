import sys, time, numpy as np
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.bits import masks_up_to
from src.step1.models.iqp import IQPModel
import src.step1.models.iqp as I
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import sample_indices
from src.step1.walsh import empirical_distribution, parity_coefficients
from src.step4.targets import iqp4_target
from src.step14.run import SIGMA
n=16; ops=masks_up_to(n,3)
seed=int(sys.argv[1]); N=int(sys.argv[2]); K=int(sys.argv[3])
p=iqp4_target(SIGMA,seed,n)[0]
fh=parity_coefficients(empirical_distribution(sample_indices(p,N,seed),n))[ops]
me=MaxEntModel(n,3); qme=me.prob(me.fit_moments(fh,ops).params)
I.K_MAX=K
t=time.time(); m=IQPModel(n,gens_mode="sparse"); f=m.fit_moments(fh,ops,seed=seed,n_restarts=3)
qs=m.prob(f.params)
Gme=M1.completion_gap(qme,p,n)["G"]; Gs=M1.completion_gap(qs,p,n)["G"]
print(f"seed {seed} N {N} K {K} kept {m.n_params}  R_sparse={Gs/Gme:.3f}  resid={f.train_residual:.2e}  {time.time()-t:.0f}s", flush=True)
