from PyQt5.QtCore import QPoint, Qt, QTime, QTimer
from PyQt5.QtGui import QColor, QPainter, QPolygon, QFont, QPen
from PyQt5.QtWidgets import QApplication, QWidget
import numpy as np
class AnalogClock(QWidget):
    secondHand = QPolygon([
        QPoint(7, 8),
        QPoint(-7, 8),
        QPoint(0, -80)
    ])
    hourHand = QPolygon([
        QPoint(7, 8),
        QPoint(-7, 8),
        QPoint(0, -50)
    ])
    minuteHand = QPolygon([
        QPoint(7, 8),
        QPoint(-7, 8),
        QPoint(0, -70)
    ])
    textColor = QColor(150, 0, 150)
    hourColor = QColor(127, 0, 127)
    minuteColor = QColor(0, 100, 250, 200)
    secondColor = QColor(195, 0, 0, 150)
    def __init__(self, parent=None):
        super(AnalogClock, self).__init__(parent)
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000)
        self.setWindowTitle("Analog Clock")
        
        self.resize(400, 400)
        pen = QPen(QColor(50,25,30))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        side = min(self.width(), self.height())
        #painter.scale(side / 200, side / 200)
        painter.save()
        painter.restore() 
    
    
    def paintEvent(self, event):
        side = min(self.width(), self.height())
        time = QTime.currentTime()
        painter = QPainter(self)
        k_x=[]
        k_y=[]
        degr=[90, 120, 150, 180, 210, 240 , 270, 300, 330, 0, 30, 60, ]
        for i in degr:                    #Skapar Urtavla timmar
            if i == 0:
                x=int(197+180*np.cos((i-90)*np.pi/180))
                y=int(205+180*np.sin((i-90)*np.pi/180))
                painter.drawText(QPoint(x, y), str(i))
            else:    
                x=int(190+180*np.cos((i-90)*np.pi/180))
                y=int(205+180*np.sin((i-90)*np.pi/180))
                painter.drawText(QPoint(x, y), str(i))
        
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200, side / 200)

    
        painter.save()
        painter.restore() 
        painter.setPen(Qt.NoPen)
        painter.save()
        print(f'hour:{time.hour()}, minute:{time.minute()}, second:{time.second()}')      
        painter.restore()
    
        painter.setPen(AnalogClock.hourColor)
        for i in range(12):                           #Skapar Urtavla timmar
            painter.drawLine(74, 0, 82, 0)
            painter.rotate(30.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(AnalogClock.minuteColor)
        painter.save()
        painter.restore()

        painter.setPen(AnalogClock.minuteColor) 
        for j in range(60):                           #Skapar Urtavla minuter
            if (j % 5) != 0:
                painter.drawLine(76, 0, 80, 0)
            painter.rotate(6.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(AnalogClock.secondColor)
        painter.save()
        painter.restore()

        painter.rotate(180)  
        painter.drawConvexPolygon(AnalogClock.secondHand)
       
        
        painter.setBrush(AnalogClock.minuteColor)
        painter.save()
        painter.restore()
    
           
   
    """
    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.drawText(event, qp)
        qp.end()
    """

    
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    clock = AnalogClock()
    clock.show()
    sys.exit(app.exec_())