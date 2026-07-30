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
        print("Enter pressed, calling validation")
        if self.validate():
            self.EndModal(wx.ID_OK)

    def on_ok(self, event):
        print("Button clicked, calling validation")
        if self.validate():
            event.Skip()

    def validate(self):
        val = self.txt.GetValue()
        try:
            float(val)
            return True
        except ValueError:
            print("Validation failed!")
            return False


app = wx.App(False)
d = MyDialog()
wx.CallAfter(d.txt.SetValue, "10300, 11450")
wx.CallAfter(lambda: d.txt.ProcessEvent(wx.CommandEvent(wx.wxEVT_TEXT_ENTER)))
wx.CallAfter(lambda: wx.CallLater(500, d.EndModal, wx.ID_CANCEL))  # Fallback chiusura
res = d.ShowModal()
print("Dialog closed with code:", res)
