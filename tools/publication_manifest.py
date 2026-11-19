"""Print one tracked file encoded for connector upload; never handles credentials."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--file')
parser.add_argument('--start',type=int)
parser.add_argument('--count',type=int,default=8)
args=parser.parse_args()
if args.start is not None:
    paths=subprocess.check_output(['git','ls-files'],cwd=root,text=True).splitlines()[args.start:args.start+args.count]
    output=[]
    for name in paths:
        data=(root/name).read_bytes()
        output.append({'path':name,'mode':'100644','type':'blob','content':data.decode('utf-8')})
    print(json.dumps(output))
elif args.file:
    path=(root/args.file).resolve()
    if not path.is_relative_to(root):raise ValueError('Path outside project')
    data=path.read_bytes()
    print(json.dumps({'path':args.file,'content':base64.b64encode(data).decode(),'encoding':'base64','text':data.decode('utf-8'),
                      'git_sha':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}))
else:
    paths=subprocess.check_output(['git','ls-files'],cwd=root,text=True).splitlines()
    print(json.dumps([{'path':path,'bytes':(root/path).stat().st_size} for path in paths]))
