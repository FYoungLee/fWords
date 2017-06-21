from PyQt5.QtWidgets import QApplication
import fWordsUI
import sys

app = QApplication(sys.argv)
w = fWordsUI.fWordsMainWindow()
app.exec_()