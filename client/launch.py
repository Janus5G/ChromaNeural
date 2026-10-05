import argparse,time,logging,sys
from logging.handlers import RotatingFileHandler
START=time.perf_counter()
def main():
    from chroma.i18n import LocaleContext,LanguagePreference,LOCALES,language_from_argv,argument_parser
    from chroma.localized_dialogs import Dialogs
    locale=LocaleContext(language_from_argv(sys.argv[1:]) or "en")
    parser=argument_parser(locale,description=locale.text("launch.help"))
    parser.add_argument("--workspace",help=locale.text("launch.workspace"))
    parser.add_argument("--state-dir",help=locale.text("launch.state"))
    parser.add_argument("--smoke-report",help=locale.text("launch.smoke"))
    parser.add_argument("--language",choices=LOCALES,help=locale.text("launch.language"))
    args=parser.parse_args()
    from chroma.settings import Settings
    settings=Settings(args.state_dir)
    locale.set(args.language or LanguagePreference(settings.directory).locale)
    handler=RotatingFileHandler(settings.directory/"client.log",maxBytes=1048576,backupCount=3,encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log=logging.getLogger("chroma");log.setLevel(logging.INFO);log.addHandler(handler)
    root=None;app=None
    try:
        from chroma.process_lifetime import protect_process_tree
        protect_process_tree()
        import tkinter as tk
        from tkinter import messagebox
        from chroma.dashboard import App
        root=tk.Tk()
        dialogs=Dialogs(root,locale)
        def callback_error(kind,error,tb):
            log.error("GUI callback failed",exc_info=(kind,error,tb))
            dialogs.showerror("ChromaNeural",locale.msg("error.callback"),parent=root)
        root.report_callback_exception=callback_error
        app=App(root,args.workspace,state_dir=settings.directory,locale=locale);root.update()
        log.info("Client started; remote execution disabled")
        if args.smoke_report:
            from scripts.dashboard_smoke import exercise
            root.after(250,lambda:exercise(app,args.smoke_report,START))
        root.mainloop();log.info("Client exited")
    except Exception:
        log.exception("Startup failed")
        if root:
            try:
                from tkinter import messagebox
                Dialogs(root,locale).showerror("ChromaNeural",locale.msg("error.startup"),parent=root)
            finally:
                if app:app.quit()
                else:root.destroy()
        raise
    finally:
        handler.close();log.removeHandler(handler)
if __name__=="__main__":main()
