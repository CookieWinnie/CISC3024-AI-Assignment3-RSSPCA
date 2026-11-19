# Mathematical correspondence and implementation choices

Let X be d by n, with one centered training observation in each column.
Paper equation (13): maximize ||X^T w||_1 subject to ||w||_2^2=1,
||w||_1 <= c1 and w^T L w <= c2. We use the authors' multiplier-based iteration;
we select eta1 and eta2 rather than attempting to map them to prescribed c1,c2.
No assertion is made that a global constrained optimum or specified budgets are attained.

L=D-A uses unit horizontal and vertical neighbor edges. With column-major flattening,
the index of pixel (row,column) is row + height*column. An explicit coordinate-distance
test verifies this construction, including boundaries. w^T L w equals the sum over
undirected neighboring pixel pairs of (w_i-w_j)^2.

Set U=diag(abs(w)) and v=X sign(X^T w). The MATLAB reference uses

u = U solve(U + eta1 I + eta2 L U, v), then w = u / ||u||_2.

The paper, equation (32), uses

u = solve(U + eta1 I + eta2 U L, U v).

These expressions are equivalent because
(U+eta1 I+eta2 U L) U = U (U+eta1 I+eta2 L U).
For eta1>0 the systems are invertible, including zero diagonal entries of U.
The Python solver uses the MATLAB form with sparse matrices and sparse direct solves.
No epsilon is inserted into abs(w); zero entries are handled by the division-free form.
Every production RSSPCA candidate has eta1>0 and eta2>0.

For positive entries of U, this is also the normalized solution of
(I + eta1 U^{-1} + eta2 L)u=v, the paper's equation (30).
eta1=lambda2/(2 lambda1), eta2=lambda3/lambda1 in the paper's multiplier notation.
The eta1=eta2=0 branch is the PCA-L1 update u=X sign(X^T w).
The smooth-only eta1=0,eta2>0 branch uses the continuous Eq. (30) extension;
that branch is not used in the reported RSSPCA experiments.

The initial directions are the columns of the original thin SVD, as in MATLAB.
After each component we apply X <- X-W(W^T X) to the current residual X with
all accumulated columns W. We preserve this unusual upstream cumulative deflation;
we do not replace it with Gram-Schmidt or an orthogonality constraint.

The reference code monitors relative change in ||X^T w||_2, even though the paper's
objective is L1. We keep its 1e-4 tolerance and 100-iteration cap for faithful translation,
and log L1 projection, L2 monitor, direction change, L1 weight, and smoothness.
Meeting this scalar monitor is not evidence of a stationary constrained L1 optimum.
Two final recognition components on seed 3024 reach the cap and are reported as such.

RSSPCA's W is not generally orthogonal. Recognition uses the reference scores W^T x.
Reconstruction uses W pinv(W) x, the Euclidean least-squares projection onto span(W),
with NumPy pinv rcond=1e-10. This is a declared evaluation change from the upstream
W W^T reconstruction. The same projector is used for every method, and no clipping
is performed before metrics. PCA's projector agrees with W W^T up to roundoff.

Tests compare the sparse update with both dense formulas (including exact zeros),
and compare three full components with an independent literal dense MATLAB transcription.
MATLAB itself was not available or run. A final 30-component ORL fit was replayed to
check its saved weights and predictions. See results/verification.json for actual checks.
