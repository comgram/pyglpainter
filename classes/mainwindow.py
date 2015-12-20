from PyQt5.QtWidgets import QMainWindow
from classes.ui_mainwindow import Ui_MainWindow
from classes.painterwidget import PainterWidget

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        self.setupUi(self)
        self.painter = PainterWidget()
        self.gridLayout1.addWidget(self.painter)