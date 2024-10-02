import sys
from PyQt5 import QtWidgets
from ui.Forms.MainForm import MainForm

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = MainForm()
    widget.show()
    sys.exit(app.exec_())
    pass
