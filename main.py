import liferpg.engine.player
print(liferpg.engine.player.__file__)

from liferpg.ui.tkinter_app import LifeRPGApp

if __name__ == "__main__":
    app = LifeRPGApp()
    app.mainloop()
