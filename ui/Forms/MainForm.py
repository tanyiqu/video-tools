from ui.Forms.Ui_MainForm import Ui_MainForm
from PyQt5.QtWidgets import QWidget

class MainForm(QWidget):
    def __init__(self, parent=None):
        super(MainForm, self).__init__(parent)
        self.mainForm = Ui_MainForm()
        self.mainForm.setupUi(self)
        pass
    pass

