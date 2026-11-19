"""Figures computed from saved measurements and model outputs."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .rss_pca import spatial_laplacian

def make_figures(root=Path('.')):
    results=root/'results'; figures=results/'figures'
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':200})
    colors={'PCA':'#295e93','PCA-L1':'#a66b27','RSSPCA':'#267b60'}
    data=pd.read_csv(results/'recognition_metrics.csv')
    summary=data.groupby(['method','components']).accuracy.agg(['mean','std']).reset_index()
    fig,ax=plt.subplots(figsize=(7.2,3.5),layout='constrained')
    for method in colors:
        sub=summary[summary.method==method]
        ax.errorbar(sub.components,100*sub['mean'],yerr=100*sub['std'],label=method,marker='o',capsize=4,color=colors[method])
    ax.set(xlabel='Number of projection vectors',ylabel='Recognition accuracy (%)',xticks=[5,10,20,30],ylim=(50,102))
    ax.grid(alpha=.2);ax.legend(loc='lower right')
    fig.savefig(figures/'accuracy_vs_components.png');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.2,3.3),layout='constrained')
    sub=summary[summary.components==30].set_index('method').loc[list(colors)]
    ax.bar(list(colors),100*sub['mean'],yerr=100*sub['std'],capsize=5,color=list(colors.values()),width=.55)
    for i,value in enumerate(sub['mean']):ax.text(i,100*value+3,f'{100*value:.2f}%',ha='center')
    ax.set(ylabel='Recognition accuracy (%)',ylim=(0,106),title='30 projection vectors; mean and sample SD across 3 splits')
    fig.savefig(figures/'accuracy_comparison.png');plt.close(fig)
    recon=pd.read_csv(results/'reconstruction_metrics.csv')
    fig,axes=plt.subplots(1,2,figsize=(8,3.2),layout='constrained')
    for ax,condition in zip(axes,['clean','occluded']):
        for method in colors:
            sub=recon[(recon.method==method)&(recon.condition==condition)]
            ax.plot(sub.components,sub.mse,marker='o',label=method,color=colors[method])
        ax.set(title=condition.title()+' test input',xlabel='Projection vectors',ylabel='MSE (intensity range 0 to 1)',xticks=[5,10,20,30]);ax.grid(alpha=.2)
    axes[1].legend(fontsize=9)
    fig.savefig(figures/'reconstruction_metrics.png');plt.close(fig)
    examples=np.load(results/'reconstruction_examples.npz')
    # Predetermined subjects, first test image for each; no ranking by quality.
    subjects=[1,11,21,31]
    selected=[int(np.flatnonzero(examples['labels']==label)[0]) for label in subjects]
    fig,axes=plt.subplots(4,4,figsize=(6.6,6.9),layout='constrained')
    for row,index in enumerate(selected):
        for col,key in enumerate(['clean','corrupted','PCA','RSSPCA']):
            axes[row,col].imshow(examples[key][:,index].reshape((56,46),order='F'),cmap='gray',vmin=0,vmax=1)
            axes[row,col].set_xticks([]);axes[row,col].set_yticks([])
            if row==0:axes[row,col].set_title({'clean':'Original','corrupted':'Occluded','PCA':'PCA','RSSPCA':'RSSPCA'}[key])
        axes[row,0].set_ylabel(f'Subject {subjects[row]}\nImage {examples["test_indices"][index]+1}',fontsize=10)
    fig.savefig(figures/'reconstruction_comparison.png');plt.close(fig)
    (results/'visual_example_selection.json').write_text(json.dumps({'rule':'First saved test image for subjects 1,11,21,31; selected without inspecting errors','subjects':subjects,'zero_based_global_indices':[int(examples['test_indices'][i]) for i in selected],'components':30},indent=2))
    fig,axes=plt.subplots(3,5,figsize=(7.4,4.7),layout='constrained')
    lap=spatial_laplacian(56,46)
    diagnostics=[]
    for row,method in enumerate(colors):
        weights=np.load(results/'models'/f'recognition_2026_{method}.npz')['weights']
        for i in range(5):
            w=weights[:,i];bound=max(abs(w.min()),abs(w.max()))
            axes[row,i].imshow(w.reshape((56,46),order='F'),cmap='RdBu_r',vmin=-bound,vmax=bound)
            axes[row,i].set_xticks([]);axes[row,i].set_yticks([])
            if row==0:axes[row,i].set_title(f'Component {i+1}',fontsize=10)
            if i==0:axes[row,i].set_ylabel(method)
        diagnostics.append({'method':method,'seed':2026,'mean_l1_weight':float(abs(weights).sum(axis=0).mean()),
                            'mean_smoothness':float(np.sum(weights*(lap@weights),axis=0).mean()),
                            'fraction_abs_below_1e-6':float(np.mean(abs(weights)<1e-6)),
                            'max_abs_off_diagonal_gram':float(abs(weights.T@weights-np.eye(30)).max())})
    fig.savefig(figures/'eigenfaces.png');plt.close(fig)
    pd.DataFrame(diagnostics).to_csv(results/'loading_diagnostics.csv',index=False)

if __name__=='__main__':make_figures()
