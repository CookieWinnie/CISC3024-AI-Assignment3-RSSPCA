from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

equations={
 'objective':r'$\max_{w}\ \|X^{T}w\|_1\quad\mathrm{s.t.}\quad\|w\|_2^2=1,\quad\|w\|_1\leq c_1,\quad w^{T}Lw\leq c_2$',
 'update1':r'$U_t=\mathrm{diag}(|w_t|),\qquad v_t=X\,\mathrm{sign}(X^{T}w_t)$',
 'update2':r'$u_{t+1}=(U_t+\eta_1 I+\eta_2 U_t L)^{-1}U_t v_t,\qquad w_{t+1}=u_{t+1}/\|u_{t+1}\|_2$',
 'reconstruction':r'$\widehat{x}=\mu+W W^{\dagger}(x-\mu),\qquad W^{\dagger}=\mathrm{pinv}(W)$'
}
for name,text in equations.items():
    fig=plt.figure(figsize=(8,0.6));fig.text(.5,.5,text,ha='center',va='center',fontsize=15)
    fig.savefig(Path('results/figures')/f'equation_{name}.png',dpi=300,bbox_inches='tight',pad_inches=.06)
    plt.close(fig)
