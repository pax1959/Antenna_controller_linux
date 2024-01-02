# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QDate, QTime, QTimer, Qt
import ephem

class MyApp(QMainWindow):

    def __init__(self):
        super().__init__()

        #self.date = QDate.currentDate()
        #self.time = QTime.currentTime()
        self.initUI()
        
        timer=QTimer(self)
        timer.timeout.connect(self.displayDateTime)
        timer.start(1000)

    def initUI(self):


        self.setWindowTitle('Date')
        self.setGeometry(300, 300, 400, 200)
        self.show()

    def displayDateTime(self):
        currentDate= QDate.currentDate()
        displayDate= currentDate.toString()
        
        currentTime = QTime.currentTime()      
        displayTime = currentTime.toString('hh:mm:ss')
        self.statusBar().showMessage(displayDate+'   '+displayTime)      

    #def AzElDegrees():
        

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())