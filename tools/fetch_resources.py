"""Download only assignment resources; all output remains in this project."""
import argparse
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]

def download(url, target):
    target = ROOT / target
    if target.exists():
        print('Preserved existing', target.name, flush=True)
        return
    req = urllib.request.Request(url, headers={'User-Agent': 'CISC3024 research reproduction'})
    with urllib.request.urlopen(req, timeout=180) as response, target.open('wb') as out:
        while chunk := response.read(1024*1024):
            out.write(chunk)
    print(target.name, target.stat().st_size, hashlib.sha256(target.read_bytes()).hexdigest(), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--office', action='store_true')
    args = parser.parse_args()
    if args.office:
        download('https://mirrors.ibiblio.org/libreoffice/portable/25.2.3/LibreOfficePortable_25.2.3_MultilingualStandard.paf.exe', 'tools/LibreOfficePortable.paf.exe')
    else:
        download('https://ndownloader.figshare.com/files/50337435', 'data/ORL.mat')
