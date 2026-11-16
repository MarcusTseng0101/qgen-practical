import json, glob, numpy as np
o = {s: json.load(open(f'results/step29/xf02/seed_{s}/metrics.json')) for s in range(1060, 1074)}
c30 = {s: json.load(open(f'explore/step30/out/xf02_given_{s}.json')) for s in range(1060, 1074)}
A = {}
for f in glob.glob('explore/step31/out/*.json'):
    d = json.load(open(f)); A.setdefault(d['arm'], {})[d['seed']] = d
rows = {}
def add(name, vals):
    v = [x for x in vals if x is not None]
    rows[name] = (len(v), sum(x < 1 for x in v), float(np.median(v)) if v else None)
S = range(1060, 1074)
add('N1e4 flow (step 29)', [o[s]['R_flow_me3'] for s in S])
add('N1e4 given (step 29)', [o[s]['R_given_me3'] for s in S])
add('N1e4 enl (step 29)', [o[s]['R_enl_me3'] for s in S])
add('N1e4 CohIQP untied (step 30)', [c30[s]['R_coh'] for s in S])
r5 = A.get('recipe5', {}); c5 = A.get('coh5', {}); gi = A.get('given_inf', {})
add('N1e5 flow', [r5[s]['G_flow'] / r5[s]['G_me3'] if s in r5 else None for s in S])
add('N1e5 given', [r5[s]['G_given'] / r5[s]['G_me3'] if s in r5 else None for s in S])
add('N1e5 enl', [r5[s]['G_enl'] / r5[s]['G_me3'] if s in r5 else None for s in S])
add('N1e5 CohIQP untied', [c5[s]['G_coh'] / c5[s]['G_me3'] if s in c5 else None for s in S])
add('Ninf given (exact moments)', [gi[s]['G_given'] / gi[s]['G_me3'] if s in gi else None for s in S])
for k, (n, w, m) in rows.items():
    print(f'{k:32s} n={n:2d} wins={w:2d} median R={m:.3f}')
print('flags N1e5 given ratio>0.75:', sum(r5[s]['ratio_given'] > 0.75 for s in r5), '/', len(r5),
      ' ratio range', min(r5[s]['ratio_given'] for s in r5), max(r5[s]['ratio_given'] for s in r5))
print('coh5 ratio range', min(c5[s]['ratio_coh'] for s in c5), max(c5[s]['ratio_coh'] for s in c5))
print('h2h N1e5 coh vs N1e5 flow:', sum(c5[s]['G_coh'] < r5[s]['G_flow'] for s in r5 if s in c5), '/', len([s for s in r5 if s in c5]))
print('h2h N1e5 coh vs N1e4 flow:', sum(c5[s]['G_coh'] / c5[s]['G_me3'] < o[s]['R_flow_me3'] for s in c5), '/', len(c5))
print('me3 G ratio N1e5/N1e4 median:', np.median([r5[s]['G_me3'] / o[s]['G_me3'] for s in r5]))
for s in S:
    print(s, 'N1e4 flow %.2f' % o[s]['R_flow_me3'], 'coh1e4 %.2f' % c30[s]['R_coh'],
          'coh1e5 %.2f' % (c5[s]['G_coh'] / c5[s]['G_me3']) if s in c5 else '',
          'flow1e5 %.2f' % (r5[s]['G_flow'] / r5[s]['G_me3']) if s in r5 else '',
          'inf %.2f' % (gi[s]['G_given'] / gi[s]['G_me3']) if s in gi else '')
