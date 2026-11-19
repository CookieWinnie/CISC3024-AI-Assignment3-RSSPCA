"""Build the English report from saved measurements with bundled python-docx."""
import csv
import json
from pathlib import Path
from statistics import mean
from docx import Document
from docx.shared import Cm, Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results'
OUT=ROOT/'submission'
OUT.mkdir(exist_ok=True)
def read_csv(name):
    with (RESULTS/name).open(newline='',encoding='utf-8') as file:return list(csv.DictReader(file))

summary=read_csv('recognition_summary.csv')
rec=read_csv('recognition_metrics.csv')
recon=read_csv('reconstruction_metrics.csv')
diagnostics=read_csv('loading_diagnostics.csv')
run=json.loads((RESULTS/'run_summary.json').read_text())
environment=json.loads((RESULTS/'environment.json').read_text())
publication=json.loads((RESULTS/'publication.json').read_text()) if (RESULTS/'publication.json').exists() else {'published':False}
doc=Document()
section=doc.sections[0]
section.page_width=Cm(21);section.page_height=Cm(29.7)
section.top_margin=Cm(1.85);section.bottom_margin=Cm(1.8)
section.left_margin=Cm(2);section.right_margin=Cm(2)
section.header_distance=Cm(.7);section.footer_distance=Cm(.7)
for name in ['Normal','Body Text','Caption','Title','Subtitle','Heading 1','Heading 2']:
    style=doc.styles[name];style.font.name='Times New Roman';style.font.color.rgb=RGBColor(0,0,0)
    style.font.size=Pt(11)
    style.paragraph_format.space_after=Pt(7)
    style.paragraph_format.line_spacing=1.08
doc.styles['Title'].font.size=Pt(25)
doc.styles['Title'].font.bold=True
doc.styles['Title'].paragraph_format.space_after=Pt(16)
doc.styles['Heading 1'].font.size=Pt(16)
doc.styles['Heading 1'].paragraph_format.space_before=Pt(0)
doc.styles['Heading 1'].paragraph_format.space_after=Pt(10)
doc.styles['Heading 2'].font.size=Pt(12)
doc.styles['Heading 2'].font.bold=True
doc.styles['Caption'].font.size=Pt(10)
doc.styles['Caption'].paragraph_format.line_spacing=1.0
header=section.header.paragraphs[0]
header.text='CISC3024 Pattern Recognition                                      AI Assignment 3'
header.style=doc.styles['Caption']
footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('Page ')
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
table_manifest=[]

def paragraph(text,style=None):
    p=doc.add_paragraph(text,style)
    p.paragraph_format.widow_control=True
    return p

def heading(text):doc.add_heading(text,level=1)
def subheading(text):doc.add_heading(text,level=2)
def new_page():doc.add_page_break()

def table(headers,rows,widths=None):
    table_manifest.append({'headers':headers,'rows':rows})
    t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER
    t.autofit=False
    if widths:
        for col,width in zip(t.columns,widths):col.width=Cm(width)
    for cell,text in zip(t.rows[0].cells,headers):cell.text=str(text)
    for row in rows:
        for cell,text in zip(t.add_row().cells,row):cell.text=str(text)
    for row_index,row in enumerate(t.rows):
        props=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');props.append(cant)
        if row_index==0:
            repeat=OxmlElement('w:tblHeader');props.append(repeat)
        for col_index,cell in enumerate(row.cells):
            if widths:cell.width=Cm(widths[col_index])
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcPr=cell._tc.get_or_add_tcPr()
            borders=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                elem=OxmlElement('w:'+edge);elem.set(qn('w:val'),'single');elem.set(qn('w:sz'),'4');elem.set(qn('w:color'),'D9D9D9');borders.append(elem)
            tcPr.append(borders)
            margins=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                elem=OxmlElement('w:'+edge);elem.set(qn('w:w'),'70');elem.set(qn('w:type'),'dxa');margins.append(elem)
            tcPr.append(margins)
            if row_index==0:
                shading=OxmlElement('w:shd');shading.set(qn('w:fill'),'E7EEF4');tcPr.append(shading)
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
                p.paragraph_format.line_spacing=1
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if col_index==0 else WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:r.font.size=Pt(10.5);r.bold=row_index==0
    paragraph('').paragraph_format.space_after=Pt(1)
    return t

def figure(filename,width,caption=None):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after=Pt(3);p.paragraph_format.keep_with_next=bool(caption)
    p.add_run().add_picture(str(RESULTS/'figures'/filename),width=Inches(width))
    if caption:paragraph(caption,'Caption')

def link(text,url):
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(5)
    hyperlink=OxmlElement('w:hyperlink');hyperlink.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
    run=OxmlElement('w:r');props=OxmlElement('w:rPr')
    color=OxmlElement('w:color');color.set(qn('w:val'),'000000');props.append(color)
    run.append(props);node=OxmlElement('w:t');node.text=text;run.append(node);hyperlink.append(run);p._p.append(hyperlink)

def recognition_summary(method,k):
    return next(row for row in summary if row['method']==method and int(row['components'])==k)
def recon_row(method,condition):
    return next(row for row in recon if row['method']==method and row['condition']==condition and int(row['components'])==30)

# Page 1
paragraph('Reproducing Robust Sparse Smooth PCA for Face Recognition and Reconstruction','Title')
paragraph('CISC3024 Pattern Recognition\nAI Assignment 3\n19 November 2026','Subtitle')
heading('1 Introduction')
paragraph('This assignment reproduces Robust Sparse Smooth Principal Component Analysis (RSSPCA), a PCA-based image representation method published in 2025 [1]. OpenAI Codex checked the literature, translated the authors’ MATLAB iteration into Python, ran controlled experiments, and generated this report. The supplied assignment explicitly requires AI to perform the programming; no student-written source code was requested.')
paragraph('The experiments support a qualified result. With 30 projection vectors, ordinary PCA achieved 97.50% mean recognition accuracy and RSSPCA achieved 97.22% over three ORL splits. On a separate reconstruction experiment with contaminated training images, RSSPCA reduced the mean squared error for occluded test inputs from 0.006925 to 0.006522, a relative reduction of about 5.82%. These are measurements from this project, rather than the original authors’ results.')
subheading('Scope of the reproduction')
paragraph('The study uses the authors’ 56 × 46 ORL resource, three classical projection methods, and a small training-only parameter search. It examines whether the robust, sparse and spatially smooth iteration offers practical benefits under a manageable computation budget. It does not reproduce the paper’s multi-database parameter sweeps or claim universal superiority.')
paragraph('All measurements, saved predictions, split indices and optimization traces are retained with the implementation. Ten numerical tests and a replay of a complete 30-component ORL fit support the implementation checks. Two final RSSPCA components reached the iteration cap, as discussed in Section 4.')

# Page 2
new_page();heading('2 AI Assisted Algorithm Search')
paragraph('The user’s initial plan proposed RSSPCA. Codex independently verified that proposal and compared recent alternatives, so the selection process was a review of an existing candidate rather than an unaided discovery. The actual search query on 19 November 2026 was “PCA robust sparse smooth principal component analysis 2024 2025 algorithm LDA face recognition”. The search returned the selected work and the two alternatives below.')
table(['Candidate','Date and status','Relevance'],[
 ['RSSPCA [1]','27 May 2025\nPLOS ONE','Image spatial regularization; MATLAB reference and ORL resource'],
 ['SCRAMBLE [4]','7 Nov 2025\nJournal article','Sparse loadings and robustness to individual contaminated cells'],
 ['Hamiltonian sparse PCA [5]','30 Mar 2025\narXiv preprint','Sparse PCA with numerical optimization and face recognition']
],[4.7,4.1,8.2])
paragraph('Codex opened the official PLOS article, its downloadable manuscript XML, the GitHub source repository, and the Figshare data record. For SCRAMBLE it inspected the publisher’s abstract and introduction; for Tran’s candidate it inspected the author’s arXiv abstract and submission metadata. The alternatives were investigated for suitability, but were not implemented or experimentally compared in this assignment.')
paragraph('SCRAMBLE is a credible alternative when individual cells in a data matrix are corrupted. Its robust loss and sparse or elastic-net penalties are optimized on a manifold, and its examples concern tribology [4]. The arXiv candidate concerns sparse PCA and face recognition, but the abstract’s numerical-method terminology was not independently validated here [5].')
paragraph('RSSPCA was retained because it connects the assignment’s computer-vision application directly to a spatial image prior and offers inspectable reference iterations. The selected article and code were verified independently. This decision reflects suitability and reproducibility; the project does not assert that RSSPCA is the newest or best PCA variant.')
subheading('Evidence retained')
paragraph('The exact query, opened sources and decision are recorded in references/research_sources.md and AI_Process_Log.md. The upstream code is pinned to commit 58ef723884b915061af2342584cbffb87f304278 [2]. A failed DOI-tool request was resolved by opening the official PLOS article URL; no search activity or experimental history was invented.')

# Page 3
new_page();heading('3 Algorithm Description')
paragraph('Let X be a d × n matrix whose columns are centered training images. A direction w maps an image to the scalar wᵀx. Conventional PCA chooses unit directions that maximize squared projected variation; the leading left singular vectors of X give an orthonormal basis. Keeping k directions reduces 2,576 pixel features to k scores.')
paragraph('Squared contributions can give unusually large observations considerable influence. PCA-L1 instead maximizes the sum of absolute projected values. This is a projection-pursuit robustness mechanism; it is distinct from decomposing a matrix into low-rank and sparse parts. RSSPCA adds sparse and spatially smooth directions to that formulation [1,2].')
figure('equation_objective.png',6.45)
paragraph('Here c₁ and c₂ are positive constraint budgets. The L1 bound on w encourages concentration on fewer pixels, while the graph penalty discourages abrupt changes between neighboring weights. L = D − A is the unweighted image Laplacian: A connects horizontal and vertical neighbors, and D contains their degrees. Consequently wᵀLw equals the sum of squared weight differences over undirected neighbor edges.')
subheading('Iterative solution')
paragraph('The authors derive an update using a minorization-maximization surrogate. With sign applied elementwise, the essential paper update is [1, equations 32–33]:')
figure('equation_update1.png',6.1)
figure('equation_update2.png',6.45)
paragraph('η₁ adjusts the sparse term relative to the L2 term; η₂ adjusts the smooth term. In the paper’s multiplier notation η₁ = λ₂/(2λ₁) and η₂ = λ₃/λ₁. Setting both to zero yields the PCA-L1 iteration. The Python implementation solves an algebraically equivalent sparse linear system and normalizes every direction.')
paragraph('Each component starts from its corresponding original SVD direction. After extraction, the reference applies X ← X − W(WᵀX) to the current residual with all accumulated columns W. This cumulative deflation is preserved. Classification uses the first k scores Wᵀx and a nearest-neighbor classifier. Reconstruction requires special care because RSSPCA directions can be nonorthogonal.')

# Page 4
new_page();heading('4 AI Assisted Implementation and Validation')
paragraph('Codex generated separate Python modules for data loading, preprocessing, graph construction, projection learning, classification, reconstruction and visualization. The core iteration is a translation of the GPL-3.0 MATLAB reference [2], not a renamed call to ordinary PCA. The full upstream license, original reference files and change notices are retained.')
paragraph('MATLAB reshapes images in column order. The Python loader therefore uses Fortran order, and a pixel at row r and column c has index r + 56c. A coordinate-distance test checks every edge of a small graph and catches accidental joins across column boundaries.')
paragraph('The MATLAB code computes U solve(U + η₁I + η₂LU, v), whereas the paper writes solve(U + η₁I + η₂UL, Uv). Multiplying out the two systems proves their equivalence. The implementation uses sparse direct solves, avoids forming inverses, and handles exact zero entries of U without inserting an arbitrary small denominator. A degenerate normalization raises a controlled error instead of returning an invented direction.')
subheading('Checks performed')
paragraph('Ten tests passed. They compare sparse and dense updates with both nonzero and exact-zero weights; compare three extracted components with an independent literal dense transcription; check graph boundaries, normalization, finite values, preprocessing, split separation, repeatability, noise counts, and metric arithmetic. MATLAB itself was not run. This is numerical and algebraic reference validation, not a cross-language engine comparison.')
paragraph('A separate audit recomputed all 36 recognition rows from saved predictions and all 12 aggregate accuracy rows. It checked 12 model files and recomputed three occluded reconstruction rows from saved arrays. Replaying the final seed-2026 RSSPCA fit reproduced its weights exactly and all predictions identically.')
subheading('Convergence and actual debugging')
paragraph('The reference stops at relative change ≤ 10⁻⁴ in the L2 projection norm, or after 100 iterations. This differs from directly monitoring its L1 objective, so the logs record both norms and direction change. Of 120 final RSSPCA components across both experiments, 118 met the scalar monitor. Components 7 and 9 for recognition seed 3024 hit the cap, with relative changes 2.77 × 10⁻⁴ and 2.11 × 10⁻⁴. Neither the monitor nor its cap certifies a stationary constrained optimum.')
paragraph('The first experiment launch failed because an old threadpoolctl package could not inspect the numerical library. Installing version 3.6.0 only in the D: virtual environment resolved it. No experiment values were filled in before successful execution. The genuine debugging and source-analysis decisions are documented in AI_Process_Log.md.')

# Page 5
new_page();heading('5 Experimental Setup')
paragraph('The Figshare ORL.mat resource [3] contains 400 grayscale images, 40 subjects and 10 images per subject. Its image array is already 56 × 46 × 400; no further resizing was performed. The original database is 112 × 92 [1,2]. Labels, counts, finite pixel values and the downloaded file’s SHA256 were checked. Pixels were divided by 255. The Figshare record states CC BY 4.0; raw data and image-bearing model arrays are excluded from public source distribution.')
table(['Setting','Actual value'],[
 ['Recognition outer splits','Seeds 2026, 3024, 77; 7 train and 3 test per subject'],
 ['Recognition inner split','5 train and 2 validation per subject; seed outer + 1'],
 ['Final train and test sizes','280 and 120 images; inner sizes 200 and 80'],
 ['Dimensions and classifier','5, 10, 20, 30; Euclidean 1-nearest-neighbor'],
 ['Recognition preprocessing','Per-pixel training mean and sample SD; zero SD set to 1'],
 ['Reconstruction preprocessing','Training mean only; separate contaminated training data'],
 ['Optimization','Tolerance 10⁻⁴; maximum 100 iterations per component']
],[5.2,11.8])
paragraph('For each recognition split, nine pairs from η₁ ∈ {0.001, 0.01, 0.1} and η₂ ∈ {0.1, 10, 1000} were scored on inner validation accuracy at k = 20. Ties favored the earlier grid pair. Selection used no outer test observations. The chosen η₁,η₂ pairs were (0.1,10), (0.1,0.1) and (0.1,0.1) for seeds 2026, 3024 and 77, respectively. Every method was refitted on all 280 training images, with statistics fitted again on that partition.')
paragraph('Reconstruction used the seed-2026 outer split and its own nine-pair search: η₁ ∈ {10⁻⁵,10⁻³,0.1}, η₂ ∈ {0.1,1,10}. Validation minimized noisy-input MSE at k = 20. The selected pair was (10⁻⁵,1). Final fitting used 56 contaminated and 224 clean training images. Every contaminated image received a uniformly positioned 14 × 12 block of independent 0/1 pixels, replacing 6.52% of that image. All 120 noisy test inputs received a block; uncorrupted test images remained ground truth. Inner, validation, final-training and final-test noise seeds were 12026, 22026, 32026 and 42026.')
paragraph('Execution used Windows, an Intel Core Ultra 7 155H with 22 logical processors, Python 3.12.4, NumPy 1.26.4, SciPy 1.13.1, scikit-learn 1.4.2, pandas 2.2.2 and Matplotlib 3.11.0. Numerical libraries were limited to one thread. The full experiment took 83.3 seconds. Exact software versions, grids and indices are saved in the configuration and results files.')

# Page 6
new_page();heading('6 Recognition Results')
rows=[]
for k in [5,10,20,30]:
    row=[str(k)]
    for method in ['PCA','PCA-L1','RSSPCA']:
        value=recognition_summary(method,k);row.append(f'{100*float(value["mean"]):.2f} ± {100*float(value["std"]):.2f}')
    rows.append(row)
table(['Components','PCA','PCA L1','RSSPCA'],rows,[3.0,4.65,4.65,4.7])
paragraph('Table 1. Accuracy in percent, mean ± sample standard deviation over three splits. The SD is in percentage points and is not a confidence interval. Each split tests 120 images.','Caption')
figure('accuracy_vs_components.png',6.35,'Figure 1. Accuracy from saved predictions. Error bars show the sample SD across the three independently generated partitions; they are not independent-subject confidence bounds.')
paragraph('At k = 30 the correct-image counts were 114,117,120 for PCA and 113,118,119 for RSSPCA. The respective means were 97.50% and 97.22%, a 0.28 percentage-point difference favoring PCA. RSSPCA had the highest mean at k = 20, but this does not justify selecting that dimension after observing test performance.')
runtime=[]
for method in ['PCA','PCA-L1','RSSPCA']:
    values=[float(row['fit_seconds_30_components']) for row in rec if row['method']==method and int(row['components'])==30]
    runtime.append([method,f'{mean(values):.3f}',f'{min(values):.3f} to {max(values):.3f}'])
table(['Method','Mean fit time in seconds','Range in seconds'],runtime,[4.0,6.0,7.0])
paragraph('Table 2. Time to fit 30 directions, including SVD initialization and iterative updates. Projection and 1-NN evaluation took approximately 0.002 seconds per method at k = 30. Timings are individual observations, not repeated performance benchmarks.','Caption')
paragraph('Clean face recognition leaves limited scope for the L1 mechanism to help. Strong regularization also discards information: the validation scores with η₂ = 1000 were consistently poor. The training-only search exposed that sensitivity without using the final test images.')

# Page 7
new_page();heading('7 Reconstruction Results')
paragraph('Every reconstruction is evaluated against the clean held-out image. With intensity range 0 to 1, MSE is the average squared error over pixels and images. PSNR is computed per image as 10 log₁₀(1/MSEᵢ), then averaged; it is not PSNR calculated from the aggregate MSE. Values are not clipped before scoring.')
figure('equation_reconstruction.png',5.95)
paragraph('W† denotes the pseudoinverse with rcond = 10⁻¹⁰. This produces a least-squares projection onto the learned span for all methods. It corrects the assumption of orthogonal directions in the upstream W Wᵀ reconstruction and is a declared change to the evaluation protocol.')
rows=[]
for method in ['PCA','PCA-L1','RSSPCA']:
    a,b=recon_row(method,'clean'),recon_row(method,'occluded')
    rows.append([method,f'{float(a["mse"]):.6f}',f'{float(b["mse"]):.6f}',f'{float(b["mean_image_psnr_db"]):.3f}'])
table(['Method','Clean input MSE','Occluded input MSE','Occluded PSNR dB'],rows,[3.0,4.5,4.8,4.7])
paragraph('Table 3. Reconstruction of 120 held-out images using 30 directions, after fitting to the same 280-image contaminated training set. These are results from one split.','Caption')
figure('reconstruction_metrics.png',6.35,'Figure 2. Reconstruction MSE for clean and occluded test inputs. All curves are computed from the saved reconstruction_metrics.csv file.')
pca=float(recon_row('PCA','occluded')['mse']);rss=float(recon_row('RSSPCA','occluded')['mse'])
paragraph(f'RSSPCA reduced occluded-input MSE by {100*(pca-rss)/pca:.2f}% relative to PCA and increased mean per-image PSNR by 0.260 dB. Its clean-input MSE was also lower. This is consistent with a useful smooth image prior under this contamination pattern, but does not isolate a causal effect of sparsity. Reconstruction model fitting took 0.039 s for PCA, 0.192 s for PCA-L1 and 0.876 s for RSSPCA; reconstructing the 120 test images took about 0.006–0.007 s at k = 30.')

# Page 8
new_page();heading('8 Visual Reconstruction Comparison')
paragraph('Examples were chosen by a fixed rule: the first saved test image for subjects 1, 11, 21 and 31. They were not selected by favorable reconstruction errors. Both methods use 30 directions from the same contaminated training set.')
figure('reconstruction_comparison.png',5.85,'Figure 3. Clean image, block-corrupted input and reconstructions from this project. Images: ORL/AT&T, via Jing Wang’s Figshare resource [3], recorded as CC BY 4.0. The display uses a common 0-to-1 grayscale range; scoring uses unmodified numerical values.')
paragraph('PCA retains visible localized noise texture in several examples; RSSPCA produces smoother faces. Smoothing also removes fine detail, so the visual comparison should be read alongside the aggregate MSE and PSNR rather than treated as proof of superior identity preservation.')

# Page 9
new_page();heading('9 Discussion and Learning Reflection')
figure('eigenfaces.png',6.35,'Figure 4. First five learned recognition directions for seed 2026. Each direction uses a symmetric display range; sign is arbitrary. Derived from the ORL/AT&T resource [3]. These are the project’s own model outputs.')
paragraph('On seed 2026, mean loading L1 norm fell from 40.33 for PCA to 18.35 for RSSPCA, while mean wᵀLw fell from 0.3315 to 0.1062. About 52.0% of RSSPCA weights had magnitude below 10⁻⁶. These diagnostics show concentrated, smoother directions without asserting exact feature selection. The maximum off-diagonal Gram entry was 0.3165 for RSSPCA, confirming that ordinary orthogonal reconstruction would be inappropriate.')
paragraph('Differences from the published experiment include a small nested parameter grid, explicit saved stratified splits, held-out noisy-input reconstruction, and the pseudoinverse projector. The reference classification script itself differs from the paper’s stated preprocessing and split protocol. One database, three overlapping image splits, one reconstruction split and two iteration-cap components limit generalization. The comparisons do not isolate robustness, sparsity and smoothness as independent causal contributions.')
subheading('What I learned')
paragraph('This first-person reflection is an AI-prepared draft grounded in the documented work. I learned to distinguish a mathematical objective from the particular numerical procedure used to optimize it. An algorithm named “PCA” need not produce orthogonal directions, and a scalar stopping monitor does not establish that the intended objective is stationary.')
paragraph('I learned that smoothness can improve reconstruction while sparsity and projection dimension can alter recognition behavior. The lower reconstruction MSE did not translate into a higher mean recognition accuracy. Keeping the same splits and classifier, fitting preprocessing only on training data, and preserving raw predictions made that difference visible.')
paragraph('AI generated the implementation and report, but its outputs still required verification. Reading the original equations and code, testing matrix identities, checking data indexing and replaying a full fit provided evidence that the reported measurements came from the implemented method. The debugging record also shows why plausible generated code alone is insufficient.')

# Page 10
new_page();heading('10 Conclusion and Source Code Availability')
paragraph('This assignment produced and tested a Python translation of the RSSPCA reference iteration and evaluated it against PCA and PCA-L1. In the completed ORL experiments, RSSPCA offered a small reconstruction benefit under the chosen occlusion protocol, while PCA retained a slightly higher mean recognition accuracy at 30 components. The saved measurements support this limited conclusion and do not establish general superiority.')
if publication.get('published'):
    paragraph('The source used for the reported experiments is publicly available at the following verified repository. It includes runnable Python code, pinned dependencies, configuration, tests, raw numerical summaries and attribution. Face data and local image-bearing artifacts are excluded.')
    link(publication['url'],publication['url'])
else:
    paragraph('The complete local source and a publication-ready source archive are supplied with this report. Public GitHub publication is pending completion of the authenticated repository-creation/upload workflow. No public URL is claimed or fabricated. The upstream repository in Reference 2 is the authors’ MATLAB code, not this assignment’s Python source. This remaining submission requirement must be resolved before final submission.')
paragraph('AI_Process_Log.md records the actual AI workflow. requirements.txt, experiments/configs/main.json, saved split indices and results/environment.json document reproduction. The local source archive is submission/CISC3024_AI_Assignment3_Source.zip. The reports have not been submitted to Moodle.')
heading('References')
refs=[
 ('[1] Wang, J., Xie, X., Zhang, L., Li, J., Cai, H., and Feng, Y. (2025). Robust sparse smooth principal component analysis for face reconstruction and recognition. PLOS ONE, 20(5), e0323281. Published 27 May 2025.','https://doi.org/10.1371/journal.pone.0323281'),
 ('[2] yuzhounh. RSSPCA. Official MATLAB source repository. Commit 58ef723884b915061af2342584cbffb87f304278; GPL-3.0. Accessed 19 November 2026.','https://github.com/yuzhounh/RSSPCA'),
 ('[3] Wang, J. (2024). Benchmark face databases for face recognition and reconstruction. Figshare. ORL.mat file 50337435; resource labeled CC BY 4.0. Accessed 19 November 2026.','https://doi.org/10.6084/m9.figshare.27643026'),
 ('[4] Pfeiffer, P., Vana-Gür, L., and Filzmoser, P. (2025). Cellwise robust and sparse principal component analysis. Advances in Data Analysis and Classification. Published 7 November 2025.','https://doi.org/10.1007/s11634-025-00656-3'),
 ('[5] Tran, L. H. (2025). Solve sparse PCA problem by employing Hamiltonian system and leapfrog method. arXiv preprint, submitted 30 March 2025.','https://arxiv.org/abs/2503.23335')
]
for text,url in refs:
    p=paragraph(text);p.paragraph_format.space_after=Pt(2)
    for r in p.runs:r.font.size=Pt(10.5)
    link(url,url)

doc.core_properties.title='Reproducing Robust Sparse Smooth PCA for Face Recognition and Reconstruction'
doc.core_properties.author=''
doc.core_properties.subject='CISC3024 Pattern Recognition AI Assignment 3'
doc.core_properties.comments='AI-generated from executed and saved experiment results.'
doc.save(OUT/'AI_Assignment3_Report.docx')
(OUT/'report_tables.json').write_text(json.dumps(table_manifest,indent=2,ensure_ascii=False),encoding='utf-8')
(OUT/'report_content.json').write_text(json.dumps({'paragraphs':[p.text for p in doc.paragraphs], 'tables':table_manifest},indent=2,ensure_ascii=False),encoding='utf-8')
print('Created',OUT/'AI_Assignment3_Report.docx')
