import wx
from main_window import MainFrame
import sys
from version import VERSION, DATE, AUTHORS, APP_NAME

print(f"Welcome! {APP_NAME} by {AUTHORS} - Version {VERSION} ({DATE})")

class App(wx.App):
    def OnInit(self):
        self.frame = MainFrame()
        return True

if __name__ == '__main__':
    app = App()
    try:
        app.MainLoop()
    except KeyboardInterrupt:
        pass
    finally:
        sys.exit(0)


