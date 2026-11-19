"""Run leakage-free recognition and held-out reconstruction experiments."""
import hashlib
import itertools
import json
import os
import platform
import sys
import time
from pathlib import Path
import importlib.metadata
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits, threadpool_info
from src.data_loader import load_orl, stratified_split
from src.preprocessing import TrainingTransform
from src.rss_pca import fit_components, spatial_laplacian
from src.baselines import fit_pca, fit_pcal1
from src.recognition import nearest_neighbor, accuracy
from src.reconstruction import corrupt_blocks, reconstruct, reconstruction_metrics

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'

def write_json(name, value):
    (RESULTS / name).write_text(json.dumps(value, indent=2), encoding='utf-8')

def fit(method, x, k, lap, params=(0, 0)):
    if method == 'PCA': return fit_pca(x, k)
    if method == 'PCA-L1': return fit_pcal1(x, k)
    return fit_components(x, k, lap, *params)

def save_fit(tag, weights, trace, info, transform):
    np.savez_compressed(RESULTS / 'models' / (tag + '.npz'), weights=weights, mean=transform.mean, scale=transform.scale)
    if trace: pd.DataFrame(trace).to_csv(RESULTS / 'optimization' / (tag + '.csv'), index=False)
    write_json('optimization/' + tag + '.json', info)

def run():
    os.chdir(ROOT)
    for name in ['models', 'optimization', 'predictions']:
        (RESULTS / name).mkdir(exist_ok=True)
    config = json.loads((ROOT / 'experiments/configs/main.json').read_text())
    start = time.perf_counter()
    x, labels, shape = load_orl()
    lap = spatial_laplacian(*shape)
    versions = {m: importlib.metadata.version(m) for m in ['numpy','scipy','scikit-learn','pandas','matplotlib','Pillow','pytest','threadpoolctl']}
    write_json('environment.json', {'python':sys.version, 'executable':sys.executable, 'platform':platform.platform(),
               'processor':platform.processor(), 'logical_cpus':os.cpu_count(), 'packages':versions,
               'threadpools':threadpool_info(), 'threads_per_blas':1, 'date_local':'2026-11-19',
               'dataset_sha256':hashlib.sha256(Path('data/ORL.mat').read_bytes()).hexdigest()})
    recognition, search, splits, statuses, noise_records = [], [], {}, {}, {}
    # Select independently for every outer split; test labels never enter tuning.
    for seed in config['seeds']:
        train, test = stratified_split(labels, 7, seed)
        inner, val = stratified_split(labels, 5, seed+1, train)
        splits[str(seed)] = {name: arr.tolist() for name, arr in [('train',train),('test',test),('inner_train',inner),('validation',val)]}
        transform = TrainingTransform().fit(x[:, inner])
        a, b = transform.transform(x[:,inner]), transform.transform(x[:,val])
        candidates = []
        for e1, e2 in itertools.product(config['recognition_eta1'], config['recognition_eta2']):
            weights, trace, info = fit('RSSPCA', a, config['validation_components'], lap, (e1,e2))
            score = accuracy(labels[val], nearest_neighbor(weights, a, b, labels[inner]))
            row = {'experiment':'recognition','seed':seed,'eta1':e1,'eta2':e2,'components':20,
                   'validation_accuracy':score,'validation_mse':None,'fit_seconds':info['seconds'],
                   'monitor_converged_components':sum(c['converged_monitor'] for c in info['components'])}
            candidates.append(row); search.append(row)
            pd.DataFrame(search).to_csv(RESULTS/'hyperparameter_search.csv',index=False)
            print(f'recognition seed={seed} eta=({e1:g},{e2:g}) val={score:.4f} fit={info["seconds"]:.2f}s',flush=True)
        # Deterministic ties prefer earlier (smaller eta1 then eta2) candidates.
        best = max(candidates, key=lambda row: row['validation_accuracy'])
        transform = TrainingTransform().fit(x[:,train])
        a, b = transform.transform(x[:,train]), transform.transform(x[:,test])
        for method in ['PCA','PCA-L1','RSSPCA']:
            weights, trace, info = fit(method,a,30,lap,(best['eta1'],best['eta2']))
            tag = f'recognition_{seed}_{method}'
            save_fit(tag,weights,trace,info,transform); statuses[tag]=info
            for k in config['components']:
                t = time.perf_counter()
                prediction = nearest_neighbor(weights[:,:k],a,b,labels[train])
                evaluation = time.perf_counter()-t
                pd.DataFrame({'image_index':test,'true_label':labels[test],'prediction':prediction}).to_csv(RESULTS/'predictions'/f'{tag}_{k}.csv',index=False)
                recognition.append({'seed':seed,'method':method,'components':k,'accuracy':accuracy(labels[test],prediction),
                                    'correct':int(np.sum(labels[test]==prediction)), 'n_test':len(test),
                                    'fit_seconds_30_components':info['seconds'],'evaluation_seconds':evaluation,
                                    'eta1':best['eta1'] if method=='RSSPCA' else 0,
                                    'eta2':best['eta2'] if method=='RSSPCA' else 0})
            print(f'FINAL recognition seed={seed} {method}: k30={recognition[-1]["accuracy"]:.4f}',flush=True)
        pd.DataFrame(recognition).to_csv(RESULTS/'recognition_metrics.csv',index=False)
        write_json('splits.json',splits)

    # Reconstruction uses the first outer split, distinct fitting from recognition.
    seed = config['reconstruction_seed']
    split = splits[str(seed)]
    train, test, inner, val = [np.array(split[k]) for k in ['train','test','inner_train','validation']]
    a_noisy, coords = corrupt_blocks(x[:,inner],shape,seed+10000,.2)
    val_noisy, coords_val = corrupt_blocks(x[:,val],shape,seed+20000,1.)
    noise_records['inner_training']={'seed':seed+10000,'coordinates':coords,'global_indices':inner.tolist()}
    noise_records['validation']={'seed':seed+20000,'coordinates':coords_val,'global_indices':val.tolist()}
    transform = TrainingTransform(standardize=False).fit(a_noisy)
    a, b = transform.transform(a_noisy), transform.transform(val_noisy)
    candidates = []
    for e1,e2 in itertools.product(config['reconstruction_eta1'],config['reconstruction_eta2']):
        weights,trace,info=fit('RSSPCA',a,20,lap,(e1,e2))
        restored=transform.inverse(reconstruct(weights,b))
        mse, psnr=reconstruction_metrics(x[:,val],restored)
        row={'experiment':'reconstruction','seed':seed,'eta1':e1,'eta2':e2,'components':20,
             'validation_accuracy':None,'validation_mse':mse,'fit_seconds':info['seconds'],
             'monitor_converged_components':sum(c['converged_monitor'] for c in info['components'])}
        candidates.append(row);search.append(row)
        pd.DataFrame(search).to_csv(RESULTS/'hyperparameter_search.csv',index=False)
        print(f'reconstruction eta=({e1:g},{e2:g}) val_mse={mse:.6f} fit={info["seconds"]:.2f}s',flush=True)
    best=min(candidates,key=lambda row:row['validation_mse'])
    noisy_train,coords=corrupt_blocks(x[:,train],shape,seed+30000,.2)
    noisy_test,coords_test=corrupt_blocks(x[:,test],shape,seed+40000,1.)
    noise_records['final_training']={'seed':seed+30000,'coordinates':coords,'global_indices':train.tolist()}
    noise_records['final_test']={'seed':seed+40000,'coordinates':coords_test,'global_indices':test.tolist()}
    write_json('noise_manifest.json',noise_records)
    transform=TrainingTransform(standardize=False).fit(noisy_train)
    a=transform.transform(noisy_train)
    recon_rows=[]
    visual={'clean':x[:,test],'corrupted':noisy_test,'test_indices':test,'labels':labels[test]}
    for method in ['PCA','PCA-L1','RSSPCA']:
        weights,trace,info=fit(method,a,30,lap,(best['eta1'],best['eta2']))
        tag=f'reconstruction_{seed}_{method}';save_fit(tag,weights,trace,info,transform);statuses[tag]=info
        for k in config['components']:
            for condition, observed in [('clean',x[:,test]),('occluded',noisy_test)]:
                t=time.perf_counter()
                restored=transform.inverse(reconstruct(weights[:,:k],transform.transform(observed)))
                seconds=time.perf_counter()-t
                mse,psnr=reconstruction_metrics(x[:,test],restored)
                recon_rows.append({'seed':seed,'method':method,'components':k,'condition':condition,'n_test':len(test),
                                   'mse':mse,'mean_image_psnr_db':psnr,'reconstruction_seconds':seconds,
                                   'fit_seconds_30_components':info['seconds'],'eta1':best['eta1'] if method=='RSSPCA' else 0,
                                   'eta2':best['eta2'] if method=='RSSPCA' else 0})
                if k==30 and condition=='occluded':visual[method]=restored
        print(f'FINAL reconstruction {method}: k30 occluded MSE={recon_rows[-1]["mse"]:.6f}',flush=True)
    np.savez_compressed(RESULTS/'reconstruction_examples.npz',**visual)
    pd.DataFrame(recon_rows).to_csv(RESULTS/'reconstruction_metrics.csv',index=False)
    rec=pd.DataFrame(recognition)
    summary=rec.groupby(['method','components']).accuracy.agg(['mean','std']).reset_index()
    summary.to_csv(RESULTS/'recognition_summary.csv',index=False)
    write_json('run_summary.json', {'completed':True,'config':config,'wall_seconds':time.perf_counter()-start,
               'recognition_summary':summary.to_dict(orient='records'), 'reconstruction_selection':best,
               'final_fit_status':statuses,'reconstruction_projection':'W @ pinv(W) @ centered_image',
               'clipped_before_metrics':False,'psnr_aggregation':'mean of per-image PSNR, data_range=1',
               'standard_deviation':'sample standard deviation across three split accuracies (ddof=1)',
               'convergence_note':'Upstream relative L2 monitor; not a proof of stationary constrained L1 optimum'})
    print(f'COMPLETED in {time.perf_counter()-start:.1f}s',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=1):run()
