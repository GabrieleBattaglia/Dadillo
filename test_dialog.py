import wx


class MyDialog(wx.Dialog):
    def __init__(self):
        super().__init__(None, title="Test")
        self.txt = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.txt.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        self.btn = wx.Button(self, wx.ID_OK, "OK")
        self.btn.Bind(wx.EVT_BUTTON, self.on_ok)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.txt)
        sizer.Add(self.btn)
        self.SetSizer(sizer)

    def on_enter(self, event):
        print("Enter pressed, simulating OK")
        event_ok = wx.CommandEvent(wx.wxEVT_BUTTON, wx.ID_OK)
        self.ProcessEvent(event_ok)

    def on_ok(self, event):
        print("Validation ran!")
        # Non chiamiamo event.Skip(), dovrebbe rimanere aperto
        # Invece stamperemo un messaggio
        print("Validation failed, but skipping skip.")


app = wx.App(False)
d = MyDialog()
# Simuliamo l'inserimento e la pressione di enter
wx.CallAfter(d.txt.SetValue, "10300, 11450")
wx.CallAfter(lambda: d.txt.ProcessEvent(wx.CommandEvent(wx.wxEVT_TEXT_ENTER)))
d.ShowModal()
print("Dialog closed!")
