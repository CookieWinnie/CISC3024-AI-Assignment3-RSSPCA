# Actual literature search and source register

Search date: 19 November 2026, Asia/Shanghai. RSSPCA was proposed in the user's supplied
plan; the AI verified that proposal and independently searched alternatives, rather
than claiming it discovered the selected paper without prior direction.

Actual web-search query:
`PCA robust sparse smooth principal component analysis 2024 2025 algorithm LDA face recognition`

Sources opened and inspected:

1. Wang, J., Xie, X., Zhang, L., Li, J., Cai, H., and Feng, Y. (2025).
   Robust sparse smooth principal component analysis for face reconstruction and recognition.
   PLOS ONE 20(5), e0323281. Published 27 May 2025.
   https://doi.org/10.1371/journal.pone.0323281
   Official HTML and downloadable XML were inspected, especially Eq. (13), (30)-(33),
   Algorithm 1 and the ORL experimental subsections. Local unmodified XML: paper.xml.
2. Official MATLAB implementation: https://github.com/yuzhounh/RSSPCA
   Pinned SHA 58ef723884b915061af2342584cbffb87f304278. Read RSSPCA.m,
   PCAL1.m, Laplacian_matrix.m, classify_RSSPCA.m, reco_RSSPCA.m, main.m,
   README.md and LICENSE. Additional baseline reference files were downloaded.
3. Pfeiffer, P., Vana-Guer, L., and Filzmoser, P. (2025).
   Cellwise robust and sparse principal component analysis.
   Advances in Data Analysis and Classification. Published 7 November 2025.
   https://doi.org/10.1007/s11634-025-00656-3
   Publisher abstract and introduction inspected. SCRAMBLE combines robust cellwise
   loss, sparse/elastic-net loadings, and Riemannian stochastic gradient optimization.
   Its data examples are tribology rather than the target ORL image reconstruction task.
4. Tran, L. H. (2025). Solve sparse PCA problem by employing Hamiltonian system
   and leapfrog method. arXiv:2503.23335, submitted 30 March 2025.
   https://arxiv.org/abs/2503.23335
   Author's arXiv abstract and metadata inspected; it is a preprint candidate addressing
   sparse PCA and face recognition using numerical optimization. Its abstract uses both
   leapfrog and Runge-Kutta terminology; no independent solver verification was done.
5. Jing Wang (2024). Benchmark face databases for face recognition and reconstruction.
   Figshare. https://doi.org/10.6084/m9.figshare.27643026
   Resource page, API metadata, file list and CC BY 4.0 label verified.

Decision: retain RSSPCA because it has a peer-reviewed 2025 publication, explicit image
spatial regularization, inspectable MATLAB iterations and an accessible ORL resource.
SCRAMBLE is also recent and credible but targets a different contamination model.
Tran's face-focused preprint is relevant but provides a less direct reproduction path
for the selected robustness-plus-spatial-smoothness question. These are suitability
judgments, not claims that RSSPCA is universally better or the newest available method.

Additional operational searches for report tooling (not algorithm selection):
`LibreOfficePortable 25.2.3 paf.exe SourceForge` and
`LibreOfficePortable 25.2.2 MultilingualAll paf.exe`.
The first SourceForge download returned HTTP 404; a LibreOffice mirror was used instead.
