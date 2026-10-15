"""Actual GUI documentation capture; isolated state, no fabricated controller."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--tools',type=Path,required=True);parser.add_argument('--state-root',type=Path,required=True)
 args=parser.parse_args();rootdir=Path(__file__).resolve().parents[1]
 assert not args.state_root.exists(),'Use a new isolated state directory'
 args.state_root.mkdir(parents=True)
 sys.path.insert(0,str(args.tools));sys.path.insert(0,str(rootdir/'client'))
 from PIL import Image,ImageDraw
 import tkinter as tk
 from chroma.dashboard import App
 from chroma.onboarding_ui import Wizard
 from chroma.i18n import packaged_version,LOCALES,NAMES
 spec=importlib.util.spec_from_file_location('capture_helper',rootdir/'packaging/localization_gui_smoke.py')
 helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 def no_network(event,values):
  if event in ('socket.connect','socket.getaddrinfo'):raise RuntimeError('Network forbidden in documentation capture')
 sys.addaudithook(no_network)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 bindings={p.relative_to(rootdir).as_posix():sha(p) for p in (rootdir/'client').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 bindings['VERSION']=sha(rootdir/'VERSION')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=rootdir,text=True).strip()
 records=[];errors=[]
 for locale in ('en','da'):
  state=args.state_root/locale
  root=tk.Tk();root.report_callback_exception=lambda t,e,b:errors.append(type(e).__name__)
  app=App(root,state_dir=state)
  try:
   root.geometry('1600x1000+20+20');root.update()
   assert app.locale.locale=='en'
   app.language_name.set(NAMES[LOCALES.index(locale)]);app.select_language();root.update()
   assert app.locale.locale==locale
   assert not app.form_cpu.get() and not app.service.value['participation']
   app.form_tray.set(False);app.save_preferences();root.update()
   assert not app.connection_panel.editor.get('1.0','end-1c')
   assert app.connection_panel.profile.value is None
   output=rootdir/'docs'/locale/'images';output.mkdir(parents=True,exist_ok=True)
   def capture(window,view):
    window.update();time.sleep(.2);window.update()
    assert not errors,errors
    image=helper.capture_view(window)
    path=output/(view+'.png');assert not path.exists();image.save(path)
    records.append({'document':'docs/'+locale+'/guide.md','filename':path.relative_to(rootdir).as_posix(),'locale':locale,'application_version':packaged_version(),'source_commit':commit,'ui_view':view,'sha256':sha(path),'size':list(image.size),'verification':'CAPTURE PASS; VISUAL REVIEW PENDING'})
   for view in ('overview','resources','activity','connection'):
    app.show_page(view);root.update()
    assert str(app.navbuttons[view]['text'])==app.locale.text('nav.'+view)
    capture(root,view)
   wizard=Wizard(root,app.locale,state,app.mcp_secrets)
   try:
    wizard.window.geometry('1100x760+40+40');wizard.window.update()
    assert not wizard.config.load()['servers']
    wizard.tabs.select(wizard.ai);capture(wizard.window,'ai-setup')
    wizard.tabs.select(wizard.mcp);capture(wizard.window,'mcp')
   finally:wizard.window.destroy()
   assert not (state/'api-connection-v1.json').exists()
   assert app.connection_panel.profile.value is None
   assert not app.service.value['participation']
  finally:
   for callback in root.tk.call('after','info'):
    root.after_cancel(callback)
   app.quit()
 result={'status':'CAPTURE PASS; VISUAL REVIEW PENDING','version':packaged_version(),'source_commit':commit,'source_hashes':bindings,'state':'isolated empty account; actual preferences save; no network or browser action','captures':records}
 (rootdir/'docs/SCREENSHOT_MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for locale in ('en','da'):
  rows=[x for x in records if x['locale']==locale]
  sheet=Image.new('RGB',(1200,3*425),'white');draw=ImageDraw.Draw(sheet)
  for i,item in enumerate(rows):
   with Image.open(rootdir/item['filename']) as im:
    im.thumbnail((590,385));x=(i%2)*600;y=(i//2)*425;sheet.paste(im,(x,y+30));draw.text((x+8,y+8),locale+' / '+item['ui_view'],fill='black')
  sheet.save(args.state_root/(locale+'-review.png'))
 print('CAPTURE PASS: 12 actual RC5 windows; visual review pending')
if __name__=='__main__':main()