# (same imports as alpha5)
import os, json, hashlib, urllib.request, subprocess, threading, time, zipfile, tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

APP_NAME = "Life RPG"
LAUNCHER_VERSION = "1.5.0-alpha6"

GITHUB_OWNER = "Hunterkilla1018"
GITHUB_REPO = "Life_RPG"

GAME_EXE = "LifeRPG.exe"
FULL_INSTALL_ZIP = "LifeRPG_full.zip"
MANIFEST_NAME = "manifest.json"

APPDATA = os.path.join(os.environ["APPDATA"], "LifeRPG")
RUNTIME = os.path.join(APPDATA, "runtime")
CONFIG_FILE = os.path.join(APPDATA, "launcher.json")
RUNTIME_MANIFEST = os.path.join(RUNTIME, MANIFEST_NAME)
UPDATE_EXE = os.path.join(RUNTIME, "LifeRPG_update.exe")
ZIP_PATH = os.path.join(RUNTIME, FULL_INSTALL_ZIP)

os.makedirs(RUNTIME, exist_ok=True)

def normalize_version(v): return v.lstrip("v").strip() if v else ""
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(8192), b""): h.update(c)
    return h.hexdigest()

def internet_available():
    try: urllib.request.urlopen("https://api.github.com", timeout=5); return True
    except: return False

def load_config():
    d={"install_dir":"","installed_version":"","close_on_launch":True}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE,"r",encoding="utf-8") as f: d.update(json.load(f))
    with open(CONFIG_FILE,"w",encoding="utf-8") as f: json.dump(d,f,indent=4)
    return d

def fetch_latest_release():
    with urllib.request.urlopen(
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest",timeout=10
    ) as r:
        return json.loads(r.read().decode())

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LIFE RPG :: SYSTEM INTERFACE")
        self.geometry("1000x700")
        self.configure(bg="#0b0f14")
        self.resizable(False, False)

        self.cfg = load_config()
        self.install_dir = tk.StringVar(value=self.cfg["install_dir"])

        self.latest_release=None
        self.manifest=None
        self.frozen=False

        self.sys=tk.StringVar(value="INITIALIZING")
        self.net=tk.StringVar(value="UNKNOWN")
        self.integrity=tk.StringVar(value="UNKNOWN")
        self.update=tk.StringVar(value="UNKNOWN")

        self._ui()
        self.after(100,self.startup_async)

    # ---------- logging ----------
    def log(self,msg):
        ts=datetime.now().strftime("%H:%M:%S")
        self.after(0,lambda:(self.console.insert("end",f"[{ts}] {msg}\n"),
                              self.console.see("end")))

    # ---------- UI ----------
    def _ui(self):
        h=tk.Frame(self,bg="#0b0f14"); h.pack(fill="x",padx=15,pady=10)
        tk.Label(h,text=f"LIFE RPG :: SYSTEM INTERFACE   v{LAUNCHER_VERSION}",
                 fg="#7ddcff",bg="#0b0f14",font=("Consolas",14,"bold")).pack(anchor="w")
        self.status=tk.Label(self,fg="#b6f0ff",bg="#0b0f14",font=("Consolas",10),anchor="w")
        self.status.pack(fill="x",padx=15)

        main=ttk.Frame(self); main.pack(fill="both",expand=True,padx=15)
        self.actions=ttk.Frame(main); self.actions.pack(pady=10)

        self.progress=ttk.Progressbar(main,mode="determinate"); self.progress.pack(fill="x",pady=5)

        lf=ttk.LabelFrame(main,text="System Log"); lf.pack(fill="both",expand=True,pady=10)
        self.console=tk.Text(lf,bg="#05070a",fg="#b6f0ff",font=("Consolas",9))
        self.console.pack(fill="both",expand=True)

        f=ttk.Frame(self); f.pack(side="bottom",pady=10)
        ttk.Entry(f,textvariable=self.install_dir,width=100).pack()
        ttk.Button(f,text="Browse…",command=self.browse).pack(pady=5)

        self._refresh()

    def _refresh(self):
        self.status.config(
            text=f"SYSTEM: {self.sys.get()} | NET: {self.net.get()} | "
                 f"INTEGRITY: {self.integrity.get()} | UPDATE: {self.update.get()}"
        )

    def clear_actions(self):
        for w in self.actions.winfo_children(): w.destroy()

    # ---------- startup ----------
    def startup_async(self):
        if self.frozen: return
        threading.Thread(target=self.startup,daemon=True).start()

    def startup(self):
        self.log("Startup check")
        self.net.set("OK" if internet_available() else "OFFLINE")
        self._refresh()
        if self.net.get()=="OFFLINE":
            self.state("NO_INTERNET"); return

        self.latest_release=fetch_latest_release()
        latest=normalize_version(self.latest_release["tag_name"])
        installed=normalize_version(self.cfg["installed_version"])
        self.log(f"Latest {latest}, Installed {installed or 'none'}")

        base=self.install_dir.get()
        if not base or not os.path.exists(base):
            self.state("NOT_INSTALLED"); return
        if installed!=latest:
            self.state("UPDATE_REQUIRED"); return

        self.load_manifest()
        if not self.manifest:
            self.state("MANIFEST_MISSING"); return
        if not self.verify(base):
            self.state("INTEGRITY_FAILED"); return

        self.state("READY")

    # ---------- states ----------
    def state(self,s):
        self.clear_actions()
        self.sys.set("READY" if s=="READY" else "BLOCKED")
        m={
            "NO_INTERNET":("OFFLINE","UNKNOWN"),
            "NOT_INSTALLED":("INSTALL REQUIRED","UNKNOWN"),
            "UPDATE_REQUIRED":("UPDATE REQUIRED","UNKNOWN"),
            "MANIFEST_MISSING":("MANIFEST MISSING","UNKNOWN"),
            "INTEGRITY_FAILED":("REPAIR REQUIRED","FAILED"),
            "READY":("NONE","VERIFIED")
        }
        self.update.set(m[s][0]); self.integrity.set(m[s][1])

        if s=="READY":
            ttk.Button(self.actions,text="LAUNCH",command=self.launch).pack()
        elif s=="NOT_INSTALLED":
            ttk.Button(self.actions,text="INSTALL",command=self.install).pack()
        elif s=="INTEGRITY_FAILED":
            ttk.Button(self.actions,text="REPAIR",command=self.install).pack()
        else:
            ttk.Button(self.actions,text="UPDATE",command=self.update_game).pack()
        self._refresh()

    # ---------- manifest ----------
    def load_manifest(self):
        a=next((x for x in self.latest_release["assets"] if x["name"]==MANIFEST_NAME),None)
        if not a: self.manifest=None; return
        urllib.request.urlretrieve(a["browser_download_url"],RUNTIME_MANIFEST)
        with open(RUNTIME_MANIFEST) as f: self.manifest=json.load(f)
        with open(os.path.join(self.install_dir.get(),MANIFEST_NAME),"w") as f:
            json.dump(self.manifest,f,indent=4)
        self.log("Manifest loaded")

    def verify(self,base):
        for p,h in self.manifest["files"].items():
            fp=os.path.join(base,p)
            if not os.path.exists(fp) or sha256(fp)!=h:
                self.log(f"VERIFY FAIL {p}"); return False
        self.log("VERIFY OK"); return True

    # ---------- actions ----------
    def browse(self):
        if self.frozen: return
        p=filedialog.askdirectory()
        if p:
            self.install_dir.set(p); self.cfg["install_dir"]=p
            with open(CONFIG_FILE,"w") as f: json.dump(self.cfg,f,indent=4)
            self.startup_async()

    def freeze(self): self.frozen=True
    def unfreeze(self): self.frozen=False

    def install(self):
        self.freeze()
        self.progress["value"]=0
        self.log("INSTALL start")
        def run():
            a=next(x for x in self.latest_release["assets"] if x["name"]==FULL_INSTALL_ZIP)
            urllib.request.urlretrieve(a["browser_download_url"],ZIP_PATH)
            with zipfile.ZipFile(ZIP_PATH) as z:
                names=z.namelist()
                for i,n in enumerate(names,1):
                    z.extract(n,self.install_dir.get())
                    self.progress["value"]=i/len(names)*100
            self.cfg["installed_version"]=normalize_version(self.latest_release["tag_name"])
            with open(CONFIG_FILE,"w") as f: json.dump(self.cfg,f,indent=4)
            self.unfreeze()
            self.startup_async()
        threading.Thread(target=run,daemon=True).start()

    def update_game(self):
        self.freeze()
        self.log("UPDATE start")
        def run():
            a=next(x for x in self.latest_release["assets"] if x["name"]==GAME_EXE)
            urllib.request.urlretrieve(a["browser_download_url"],UPDATE_EXE)
            os.replace(UPDATE_EXE,os.path.join(self.install_dir.get(),GAME_EXE))
            self.cfg["installed_version"]=normalize_version(self.latest_release["tag_name"])
            with open(CONFIG_FILE,"w") as f: json.dump(self.cfg,f,indent=4)
            self.unfreeze()
            self.startup_async()
        threading.Thread(target=run,daemon=True).start()

    def launch(self):
        subprocess.Popen([os.path.join(self.install_dir.get(),GAME_EXE)])
        if self.cfg["close_on_launch"]: self.destroy()

if __name__=="__main__":
    Launcher().mainloop()
