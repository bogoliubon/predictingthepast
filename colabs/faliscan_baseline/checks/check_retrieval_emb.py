"""Do the stored retrieval embeddings match this checkpoint + averaging?"""
import pickle, random, sys
import numpy as np
sys.path.insert(0, '/home/cw862/predictingthepast/colabs')
from predictingthepast.eval import inference
from run_swap_inference import load_checkpoint
_, _, alphabet, params, forward = load_checkpoint('checkpoint.pkl')
dataset = inference.load_dataset('dataset.json')
emb = pickle.load(open('dataset_emb.pkl', 'rb'))
print('stored:', len(emb), 'keys of one entry:', list(next(iter(emb.values())).keys()))
rng = random.Random(0)
ids = [i for i in emb if i in dataset and 25 <= len(dataset[i]['text']) <= 200]
cos = lambda a, b: float(a @ b / np.linalg.norm(a) / np.linalg.norm(b))
for i in rng.sample(ids, 12):
  t = dataset[i]['text']
  for mode in ('avg', 'first'):
    try:
      e = inference._generate_text_emb(params, forward, alphabet, t, emb_mode=mode)
    except Exception as ex:
      print(i, 'error', repr(ex)[:100]); break
    st = emb[i]
    print(i, 'test' if i % 10 in (3, 4) else 'train', len(t), mode,
          ' '.join(f'vs stored {k}: {cos(e, np.asarray(st[k])):.4f}' for k in st if np.asarray(st[k]).shape == e.shape))
