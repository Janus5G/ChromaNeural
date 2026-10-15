import shutil,subprocess,sys,tkinter
assert sys.version_info >= (3,14)
assert shutil.which('pyw.exe')
r=subprocess.run(['node.exe','--version'],capture_output=True,text=True,check=True,timeout=15)
assert int(r.stdout.strip().lstrip('v').split('.')[0]) >= 24
