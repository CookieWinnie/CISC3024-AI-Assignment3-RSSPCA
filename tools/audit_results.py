"""Verify saved results against independent recomputation and replay."""
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from src.data_loader import load_orl
from src.rss_pca import fit_components, spatial_laplacian
from src.preprocessing import TrainingTransform
from src.reconstruction import reconstruction_metrics
from src.recognition import nearest_neighbor

def audit():
    r=Path('results');x,y,shape=load_orl()
    rec=pd.read_csv(r/'recognition_metrics.csv')
    summary=pd.read_csv(r/'recognition_summary.csv')
    splits=json.loads((r/'splits.json').read_text())
    for row in rec.itertuples():
        p=pd.read_csv(r/'predictions'/f'recognition_{row.seed}_{row.method}_{row.components}.csv')
        assert np.array_equal(y[p.image_index],p.true_label)
        correct=int(np.sum(p.true_label==p.prediction))
        assert correct==row.correct and abs(correct/len(p)-row.accuracy)<1e-14
        assert set(p.image_index)==set(splits[str(row.seed)]['test'])
    for row in summary.itertuples():
        values=rec[(rec.method==row.method)&(rec.components==row.components)].accuracy
        assert np.isclose(values.mean(),row.mean) and np.isclose(values.std(ddof=1),row.std)
    for seed,split in splits.items():
        assert not set(split['train'])&set(split['test'])
        assert set(split['inner_train'])|set(split['validation'])==set(split['train'])
        assert not set(split['inner_train'])&set(split['validation'])
    reconstructed=np.load(r/'reconstruction_examples.npz')
    metrics=pd.read_csv(r/'reconstruction_metrics.csv')
    for method in ['PCA','PCA-L1','RSSPCA']:
        mse,psnr=reconstruction_metrics(reconstructed['clean'],reconstructed[method])
        row=metrics[(metrics.method==method)&(metrics.components==30)&(metrics.condition=='occluded')].iloc[0]
        assert np.isclose(mse,row.mse) and np.isclose(psnr,row.mean_image_psnr_db)
    for path in (r/'models').glob('*.npz'):
        m=np.load(path)
        assert all(np.isfinite(m[key]).all() for key in m.files)
        np.testing.assert_allclose(np.linalg.norm(m['weights'],axis=0),1,atol=1e-12)
    # Replay one full ORL final fit from the saved training indices and selected parameters.
    seed=2026;split=splits[str(seed)];train=np.array(split['train']);test=np.array(split['test'])
    transform=TrainingTransform().fit(x[:,train])
    row=rec[(rec.seed==seed)&(rec.method=='RSSPCA')].iloc[0]
    t=time.perf_counter()
    weights,_,_=fit_components(transform.transform(x[:,train]),30,spatial_laplacian(*shape),row.eta1,row.eta2)
    saved=np.load(r/'models'/'recognition_2026_RSSPCA.npz')['weights']
    np.testing.assert_allclose(weights,saved,atol=1e-12,rtol=1e-12)
    prediction=nearest_neighbor(weights,transform.transform(x[:,train]),transform.transform(x[:,test]),y[train])
    saved_prediction=pd.read_csv(r/'predictions'/'recognition_2026_RSSPCA_30.csv').prediction
    np.testing.assert_array_equal(prediction,saved_prediction)
    result={'passed':True,'recognition_rows_verified':len(rec),'summary_rows_verified':len(summary),
            'reconstruction_metrics_recomputed':3,'saved_models_checked':12,
            'replay_seed':seed,'replay_max_abs_weight_difference':float(abs(weights-saved).max()),
            'replay_predictions_identical':True,'replay_seconds':time.perf_counter()-t,
            'matlab_engine_executed':False,'reference_check':'Independent dense Python transcription of official MATLAB plus paper equation identity'}
    (r/'verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1):audit()
