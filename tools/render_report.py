"""Run the bundled DOCX renderer while retaining all temporary directories.

This local wrapper respects the user's ban on bulk deletion. It neither changes
the managed skill nor removes renderer intermediates. Use the bundled Python.
"""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ['TEMP']=os.environ['TMP']=str(ROOT/'tmp')
os.environ['PYTHONDONTWRITEBYTECODE']='1'
tempfile.tempdir=str(ROOT/'tmp')

class RetainedTemporaryDirectory:
    @classmethod
    def __class_getitem__(cls, item):return cls
    def __init__(self, suffix=None, prefix=None, dir=None, **kwargs):
        self.name=tempfile.mkdtemp(suffix=suffix or '',prefix=prefix or 'retained_',dir=dir or ROOT/'tmp')
    def __enter__(self):return self.name
    def __exit__(self,*args):pass
    def cleanup(self):pass

tempfile.TemporaryDirectory=RetainedTemporaryDirectory
office=ROOT/'tools/office-extract/App/libreoffice/program'
os.environ['PATH']=str(office)+os.pathsep+os.environ['PATH']
skill=Path('C:/Users/cookie/.codex/plugins/cache/openai-primary-runtime/documents/26.1118.11504/skills/documents/render_docx.py')
spec=importlib.util.spec_from_file_location('managed_document_renderer',skill)
renderer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
sys.argv=[str(skill),str(ROOT/'submission/AI_Assignment3_Report.docx'),
          '--output_dir',str(ROOT/'submission/rendered'),'--emit_pdf','--dpi','135','--verbose']
renderer.main()
pdf=ROOT/'submission/rendered/AI_Assignment3_Report.pdf'
(ROOT/'submission/AI_Assignment3_Report.pdf').write_bytes(pdf.read_bytes())
