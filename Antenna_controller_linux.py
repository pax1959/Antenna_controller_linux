# -*- coding: utf-8 -*-





# Fungerande version. Lagt till pulsräknare vid manuell elevering för att kunna skapa en bättre eleveringstabell.
# Korrigering: Rikta in antennen mot månen. Skriv därefter in det korrekta gradtalet i CSV-filen för det pulsnumret som står i displayen.
#        
# Version 2022-07-03: Bytt ut CSV-fil med gradtal till en uppdaterad version baserad på beräknade värden.

# 2023-12-10: Portad till Linux. Krävdes att justera installera modulen serial koden och lägga till tty och dialout i groups.
# Det finns bra instruktioner på Youtube sök 'Python serial Linux'. Portnamn för Auruino i Linux är ttyACM0. Se kod nedan. 

# 2023-12-25 Laborerat med git / github 

# 2024-02-02 Anslutit till Git-GiHub (GitHub repository: Antenna_controller_linux) 

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit
from PyQt5.QtCore import QPoint, Qt, QTime, QTimer, QPoint
from PyQt5 import uic
from PyQt5.QtGui import QColor, QPainter, QPolygon, QFont, QPen
import ephem
import serial
import datetime
import csv
import time

__version__ = '2023-12-10'
__author__  = 'Peter Axelberg'

class MyApp(QWidget):

    #det är i __init__(self) som applikationen utgår ifrån.
    #här ska all kod finnas som ska återupprepas hela tiden.
    #denna kod genomlöps i varje loop-varv.
    def __init__(self):
        super().__init__()
        
        uic.loadUi('gui_version_2023-03-06.ui',self)

        self.infoTxt=""        
        self.setWindowTitle('SM6GYB Antenna Controller 2023-12-25 - Linux')
        self.lblInfoTxt.setText('')
        self.lblDateTime.setText('')
        
        #Här används timer för att kalla på funktionen Az_El_date_time()
        #som returnerar skriver ut Az och El i grader:
        timer=QTimer(self)
        timer.timeout.connect(self.Az_El_date_time)  #Hämtar ett nytt värde på Az och El
        timer.start(1000) #uppdateras varje sekund 

        timer2=QTimer(self)
        timer2.timeout.connect(self.displayDateTimeNow)  
        timer2.start(1000) #uppdateras varje sekund 
        
        timer3=QTimer(self)
        timer3.timeout.connect(self.update)
        timer3.start(200)
        

        timer_read_arduino=QTimer(self)
        timer_read_arduino.timeout.connect(self.readSerialData)  #Hämtar ett nytt värde på Az och El
        timer_read_arduino.start(50) #uppdateras varje 50:e ms 

        self.azimuthCW.clicked.connect(self.azCW)
        
        self.azimuthCCW.clicked.connect(self.azCCW)
        
        self.eleveringUpp.clicked.connect(self.elUP)
        
        self.eleveringNed.clicked.connect(self.elDWN)
        
        self.autoTrack.clicked.connect(self.autoTrackRoutine)
        
        self.PushBtnAvsluta.clicked.connect(self.closeApp)

        with open("COM-port.csv",'r') as file_3:               #Elevering: Läs in tabell med puls <-> grader
            csv_reader = csv.reader(file_3, delimiter=';')        
            for rad in csv_reader:
                self.port=rad[0]

        
        self.seriport = serial.Serial(port='/dev/ttyACM0',
                                      baudrate=9600,
                                      parity=serial.PARITY_NONE,
                                      stopbits=serial.STOPBITS_ONE,
                                      bytesize=serial.EIGHTBITS,
                                      timeout=5)

        self.ADC_to_grader_tabell = []
        self.ADC_value=0
        self.azCW_flag     = True
        self.azCCW_flag    = True
        self.min_ADC_value = 188
        self.max_ADC_value = 710
        self.pulse_value= []
        self.pulse_value_str= []
        self.degr_pulses_table = []
        self.EL_UP_flag    = True
        self.EL_DWN_flag   = True
        self.EL_UP_flag_2  = False
        self.EL_DWN_flag_2 = False
        self.EL_pulse_value_from_file= 0.0         #pulsvärde som lagrats på fil --> innehåller aktuellt pulsvärde när ingen elevering pågår
        self.EL_pulse_from_sensor  = 0.0
        self.EL_gradtal =0.0
        self.EL_filename_pulse="pulse_value.csv"

        self.compass_gradtal=0
        self.elevation_gradtal=0

        self.Az=0.0
        self.El=0.0
        self.Az_El_date_time()
       
        self.Az_diff = 5.0                       #Antal grader innan autotracking justerar Azimuth
        self.EL_diff = 5.0                       #Antal grader innan autotracking justerar Elivering
        self.EL_max  = 45
        self.EL_min  = 2
        self.Az_max  = 360
        self.Az_min  = 0
        with open("degr_pulse_table_teoretisk.csv",'r') as file_2:               #Elevering: Läs in tabell med puls <-> grader
                csv_reader = csv.reader(file_2, delimiter=';')        
                for rad in csv_reader:
                    temp=[rad[0],float(rad[1])]
                    self.degr_pulses_table.append(temp)      
           
        self.EL_pulse_value_from_file=self.read_file(self.EL_filename_pulse)
        self.EL_gradtal=self.to_degr(self.EL_pulse_value_from_file,self.degr_pulses_table)
        
        self.lblAntennaElevation.setText(str(self.EL_gradtal))
        self.elevation_gradtal=float(self.EL_gradtal)

        with open("ADC_to_grader_tabell_2023-03-26.csv",'r') as file_3:            #Azimuth: Läs in tabell med ADC <-> grader
                csv_reader = csv.reader(file_3, delimiter=';')        
                for rad in csv_reader:
                    temp=[rad[0],float(rad[1])]
                    self.ADC_to_grader_tabell.append(temp)      
 
        #Start: Skriv ut aktuellt Azimuth-värde: 
        serial_line = self.seriport.readline() 
        str_msg= serial_line.decode('utf-8').strip()
        el_index=str_msg.find('E')
        az_adc_value=str_msg[1:el_index]               #Aktuellt ADC-värde (str)
        if az_adc_value =='':                          #förhindra error om el_pulse_count inte innehåller ett heltal
            az_adc_value ='0'
        self.ADC_value=int(az_adc_value)    
        self.ADC_gradtal=self.to_degr(self.ADC_value, self.ADC_to_grader_tabell)
        #print('az_adc_value, self.ADC_value, self.ADC_gradtal',az_adc_value, self.ADC_value,self.ADC_gradtal)
        self.lblAntennaAzimuth.setText(str(self.ADC_gradtal)+"/"+str(self.ADC_value))
        self.compass_gradtal=float(self.ADC_gradtal)
        #End: Skriv ut aktuellt Azimuth-värde:
    
        
    def to_degr(self, pulse_value, table):
        gradtal=0
        for index,rad in enumerate(table):   
            if pulse_value <  table[index][1] :            
               pulse_abs1 = np.abs(pulse_value-table[index-1][1])
               pulse_abs2 = np.abs(pulse_value-table[index][1])
               #print('pulse_abs1, pulse_abs2,index-1 -- index',pulse_abs1, pulse_abs2,index-1,index,self.ADC_to_grader_tabell[index-1][1],self.ADC_to_grader_tabell[index][1])
               if pulse_abs1 <= pulse_abs2:
                   gradtal=table[index-1][0]
               else:
                   gradtal = table[index][0]
               break
        return gradtal
         

    def write_file(self, fileName, value_to_file):
        with open (fileName,'w',newline="") as file:
            csv_writer=csv.writer(file,delimiter=";")
            csv_writer.writerow([str(value_to_file)])
        

    def read_file(self,fileName):
        
        with open(fileName,'r') as file:
            csv_reader = csv.reader(file, delimiter=';')        
            pulse_value=[]
            for rad in csv_reader:
                pulse_value.append(rad)
                #print('YYY',pulse_value, fileName)
        return float(pulse_value[0][0])


    def elUP(self):
        
        if self.EL_UP_flag==True:
            #print('UP_self.EL_gradtal_början',self.EL_gradtal)
            self.EL_pulse_value_from_file=self.read_file(self.EL_filename_pulse)
            #print("self.EL_pulse_value_from_file_UP=",self.EL_pulse_value_from_file)
            self.EL_gradtal=self.to_degr(self.EL_pulse_value_from_file,self.degr_pulses_table)
            self.lblAntennaElevation.setText(str(self.EL_gradtal))
            self.elevation_gradtal=float(self.EL_gradtal)
            #print('UP_self.EL_gradtal_efter',self.EL_gradtal)
            self.seriport.write(b"EL_UP;")                               #Startar elevering UPP
            self.infoTxt="Altitude UP"
            self.lblInfoTxt.setText(self.infoTxt)
            self.eleveringNed.setEnabled(False)
            self.EL_UP_flag_2=True                                       #Används i readSerialData för att starta fkn find_Altitud_UP
            self.EL_UP_flag=False
        else:    
            self.EL_pulse_value_from_file = self.EL_pulse_value_from_file + self.EL_pulse_from_sensor
            self.lblInfoTxt.setText("Altitude Stop")
            self.seriport.write(b"EL_stop;") 
            self.eleveringNed.setEnabled(True)
            self.infoTxt=""
            self.lblInfoTxt.setText(self.infoTxt)
            self.EL_UP_flag=True
            self.EL_UP_flag_2=False                                      #Används i readSerialData för att stoppa fkn find_Altitud_UP
            #print('Innan skrivning till fil:', self.EL_pulse_value_from_file)
            self.write_file(self.EL_filename_pulse, self.EL_pulse_value_from_file)




    def elDWN(self):
        if self.EL_DWN_flag==True:
            #print('DWN_self.EL_gradtal_början',self.EL_gradtal)

            self.EL_pulse_value_from_file = self.read_file(self.EL_filename_pulse)
            print("self.EL_pulse_value_from_file_DWN=",self.EL_pulse_value_from_file)
            self.EL_gradtal=self.to_degr(self.EL_pulse_value_from_file,self.degr_pulses_table)
            self.lblAntennaElevation.setText(str(self.EL_gradtal))
            self.elevation_gradtal=float(self.EL_gradtal)
            #print('DWN_self.EL_gradtal_efter',self.EL_gradtal)
            self.lblInfoTxt.setText("Altitude DWN")
            self.seriport.write(b"EL_DWN;")                              #Startar elevering NED
            self.eleveringUpp.setEnabled(False)
            self.infoTxt="Altitude Down"
            self.lblInfoTxt.setText(self.infoTxt)
            self.EL_DWN_flag=False
            self.EL_DWN_flag_2=True
        else:
            self.EL_pulse_value_from_file = self.EL_pulse_value_from_file - self.EL_pulse_from_sensor
            self.lblInfoTxt.setText("Altitude Stop")
            self.seriport.write(b"EL_stop;") 
            self.eleveringUpp.setEnabled(True)
            self.EL_DWN_flag=True
            self.EL_DWN_flag_2=False
            self.infoTxt=""
            self.lblInfoTxt.setText(self.infoTxt)
            self.write_file(self.EL_filename_pulse, self.EL_pulse_value_from_file)

            
    def azCW(self):
        if self.azCW_flag==True:                     
            self.seriport.write(b"Az_CW;") 
            self.azimuthCCW.setEnabled(False)
            self.infoTxt="Turning CW"
            self.lblInfoTxt.setText(self.infoTxt)
            self.azCW_flag   =False

        else:
            self.seriport.write(b"Az_stop;") 
            self.azimuthCCW.setEnabled(True)
            self.infoTxt="Stop Turning CW"
            self.lblInfoTxt.setText(self.infoTxt)
            self.azCW_flag    = True


    def azCCW(self):
        if self.azCCW_flag==True:
            self.seriport.write(b"Az_CCW;") 
            self.azimuthCW.setEnabled(False)
            self.infoTxt="Turning CCW"
            self.lblInfoTxt.setText(self.infoTxt)
            self.azCCW_flag  = False

        else:
            self.lblInfoTxt.setText("Rotation STOP")
            self.seriport.write(b"Az_stop;")
            self.azimuthCW.setEnabled(True)
            self.infoTxt=""
            self.lblInfoTxt.setText(self.infoTxt)
            self.azCCW_flag  = True


    def autoTrackRoutine(self):
        self.AutoTrack_Az_CW_flag=False
        self.AutoTrack_Az_CCW_flag=False
        self.AutoTrack_EL_UP_flag=False
        self.AutoTrack_EL_DWN_flag=False
        if self.autoTrack.isChecked() == True:
            self.lblInfoTxt.setText("AutoTracking ...")
            self.azimuthCW.setEnabled(False)
            self.azimuthCCW.setEnabled(False)
            self.eleveringUpp.setEnabled(False)
            self.eleveringNed.setEnabled(False)
        else:
            self.azimuthCW.setEnabled(True)
            self.azimuthCCW.setEnabled(True)
            self.eleveringUpp.setEnabled(True)
            self.eleveringNed.setEnabled(True)
            self.EL_pulse_value_from_file = self.read_file(self.EL_filename_pulse)
            self.lblAntennaElevation.setText(str(self.EL_pulse_value_from_file))
            self.lblInfoTxt.setText('-- Manuell vridning --') 
            
    def ledBlink(self):
        print("LED_BLINK")
        self.lblInfoTxt.setText("LED_BLINK")
        self.seriport.write(b"LED_BLINK;") 

    def readSerialData(self):
        serial_line = self.seriport.readline() 
        str_msg= serial_line.decode('utf-8').strip()
        print(str_msg)
        """ ************************** K O D   F Ö R   A Z I M U T H    B Ö R J A R    H Ä R *******************"""
        el_index=str_msg.find('E')
        az_adc_value=str_msg[1:el_index]               #Aktuellt ADC-värde (str)
        if az_adc_value =='':                        #förhindra error om el_pulse_count inte innehåller ett heltal
            az_adc_value ='0'
        self.ADC_value=int(az_adc_value)
        
        self.ADC_gradtal=self.to_degr(self.ADC_value,self.ADC_to_grader_tabell)   #Konvertera ADC-värde till grader    
        self.ADC_gradtal_float = float(self.ADC_gradtal)
        
        """ ************************** K O D   F Ö R   E L E V E R I N G    B Ö R J A R    H Ä R *******************"""
        el_pulse_count=str_msg[el_index+1:]            #Aktuellt Puls-värde (str)
        if el_pulse_count =='':                        #förhindra error om el_pulse_count inte innehåller ett heltal
            el_pulse_count ='0'
        self.EL_pulse_from_sensor=int(el_pulse_count)

        
        """ ******************************************   Autotracking:  *********************************************"""
     

        """  ************************   Azimuth:  **********************"""
        if self.autoTrack.isChecked() == True:         #Autotracking: True--> Yes
            if self.ADC_gradtal_float-self.Az < -self.Az_diff and self.Az> 0:
                self.AutoTrack_Az_CW_flag=True
                self.seriport.write(b"Az_CW;")         #Antennen ligger efter månens position. Vrid antennen Az_CW
                self.infoTxt="-- AutoTracking -- Turning CW --"

            if self.AutoTrack_Az_CW_flag==True: 
                if (self.ADC_gradtal_float-self.Az)>=0 or (self.ADC_gradtal_float)>= self.Az_max:              #stäng av Az_CW-vridning   
                    self.seriport.write(b"Az_stop;")
                    self.AutoTrack_Az_CW_flag = False
                    if (self.ADC_gradtal_float) >= self.Az_max:
                        self.infoTxt="-- Antennen i CW ändläge -- "
                    else:
                        self.infoTxt="-- AutoTracking -- "


            if self.ADC_gradtal_float-self.Az > self.Az_diff and self.Az> 0:
                self.AutoTrack_Az_CCW_flag=True
                self.seriport.write(b"Az_CCW;")         #Antennen ligger före månens position. Vrid antennen Az_CCW
                self.infoTxt="-- AutoTracking -- Turning CCW --"
               

            if self.AutoTrack_Az_CCW_flag==True: 
                if (self.ADC_gradtal_float-self.Az) <=0 or (self.ADC_gradtal_float)<= self.Az_min:             #stäng av Az_CCW-vridning
                    self.seriport.write(b"Az_stop;")
                    self.AutoTrack_Az_CCW_flag = False
                    if (self.ADC_gradtal_float) <= self.Az_min:
                        self.infoTxt="-- Antennen i CCW ändläge -- "
                    else:
                        self.infoTxt="-- AutoTracking -- "
            self.lblAntennaAzimuth.setText(str(self.ADC_gradtal)+"/"+str(self.ADC_value))
            self.compass_gradtal=float(self.ADC_gradtal)

            """  ************************   Elevering:  **********************"""  
            self.EL_pulse_value_from_file = self.read_file(self.EL_filename_pulse)
            
            if float(self.to_degr(self.EL_pulse_value_from_file,self.degr_pulses_table)) - self.El <-self.EL_diff:      #Antennens elevering lägre än månens position --> öka elevering
                self.seriport.write(b"EL_UP;")
                self.AutoTrack_EL_UP_flag=True
                self.infoTxt="-- AutoTracking -- Altitude UP --"
 
            if self.AutoTrack_EL_UP_flag == True:
                self.lblAntennaElevation.setText(str(float(self.to_degr(self.EL_pulse_value_from_file+self.EL_pulse_from_sensor,self.degr_pulses_table))))
                if ((float(self.to_degr(self.EL_pulse_value_from_file+self.EL_pulse_from_sensor,self.degr_pulses_table))-self.El)>=0 )  or  (float(self.to_degr(self.EL_pulse_value_from_file+self.EL_pulse_from_sensor,self.degr_pulses_table))) >= self.EL_max:                
                    time.sleep(1)
                    self.seriport.write(b"EL_stop;")    #Se till att elevering av antenn är stoppad
                    self.seriport.write(b"EL_stop;")                             #stoppar elevering UPP
                    self.AutoTrack_EL_UP_flag=False
                    self.write_file(self.EL_filename_pulse, (self.EL_pulse_value_from_file+self.EL_pulse_from_sensor))
                    self.infoTxt="-- AutoTracking ..."
                
            if float(self.to_degr(self.EL_pulse_value_from_file,self.degr_pulses_table))-self.El > self.EL_diff:      #Antennens elevering lägre än månens position --> öka elevering
                self.seriport.write(b"EL_DWN;")                                #Startar elevering NED                
                self.AutoTrack_EL_DWN_flag=True
                self.infoTxt="-- AutoTracking -- Altitude DOWN --"
                
            if self.AutoTrack_EL_DWN_flag == True:
                self.lblAntennaElevation.setText(str(float(self.to_degr(self.EL_pulse_value_from_file-self.EL_pulse_from_sensor,self.degr_pulses_table))))
                #print('RRRR',float(self.to_degr(self.EL_pulse_value_from_file-self.EL_pulse_from_sensor,self.degr_pulses_table)))
                if (float(self.to_degr(self.EL_pulse_value_from_file-self.EL_pulse_from_sensor,self.degr_pulses_table))-self.El)<=0  or  (float(self.to_degr(self.EL_pulse_value_from_file-self.EL_pulse_from_sensor,self.degr_pulses_table))) <= self.EL_min:
                    time.sleep(1)
                    self.seriport.write(b"EL_stop;")    #Se till att elevering av antenn är stoppad
                    self.seriport.write(b"EL_stop;")
                    self.AutoTrack_EL_DWN_flag = False
                    self.write_file(self.EL_filename_pulse, (self.EL_pulse_value_from_file-self.EL_pulse_from_sensor))
                    self.infoTxt="-- AutoTracking --"                

            self.lblInfoTxt.setText(self.infoTxt)
             
        else: #Manuell vridning
            #print("innan tabell",self.EL_pulse_from_sensor)
            if self.EL_UP_flag_2 == True:
                self.EL_gradtal =0.0
                self.EL_gradtal = self.to_degr(self.EL_pulse_value_from_file+self.EL_pulse_from_sensor,self.degr_pulses_table) #Konvertera aktuellt pulsvärde till grader uppåtgående
                self.lblAntennaElevation.setText(str(self.EL_gradtal)+" / "+str(self.EL_pulse_value_from_file+self.EL_pulse_from_sensor))
                self.elevation_gradtal=float(self.EL_gradtal)
                #self.find_Altitud_UP()
            if self.EL_DWN_flag_2 == True:
                #self.find_Altitud_DWN()
                self.EL_gradtal =0.0
                self.EL_gradtal = self.to_degr(self.EL_pulse_value_from_file-self.EL_pulse_from_sensor,self.degr_pulses_table) #Konvertera aktuellt pulsvärde till grader nedåtgående
                self.lblAntennaElevation.setText(str(self.EL_gradtal)+" / "+str(self.EL_pulse_value_from_file-self.EL_pulse_from_sensor))
                self.elevation_gradtal=float(self.EL_gradtal)
            
            self.lblAntennaAzimuth.setText(str(self.ADC_gradtal)+"/"+str(self.ADC_value))
            self.compass_gradtal=float(self.ADC_gradtal)
        
    def closeApp(self):
        self.seriport.write(b"Az_stop;")    #Se till att vridning av antenn är stoppad
        time.sleep(1)
        self.seriport.write(b"EL_stop;")    #Se till att elevering av antenn är stoppad
        self.seriport.close()
        self.close()
        app.quit()
        #Här behövs mera cleaning-up: Stäng av motorerna, spara El-värdet

    # Aktuellt Datum och klockslag:
    def displayDateTimeNow(self):
        now=datetime.datetime.now()
        displayDateTime=now.strftime("%Y-%m-%d %H:%M:%S")
        #t=datetime.datetime(now.year,now.month,now.day,now.hour,now.minute)
        #UTCDateTime = t.strftime('%Y/%m/%d %H:%M')           
        self.lblDateTime.setText(displayDateTime)
        
    # Beräknar och skriver ut månens position:  
    def Az_El_date_time(self):   
        now=datetime.datetime.utcnow()
        g = ephem.Observer()    
        g.long=ephem.degrees('12.54089')    #longitud JO67gw 
        g.lat=ephem.degrees('57.92943')     #latitud JO67gw
        t=datetime.datetime(now.year,now.month,now.day,now.hour,now.minute)
        g.date = t.strftime('%Y/%m/%d %H:%M')   
        m = ephem.Moon()
        m.compute(g)    
        
        self.Az=float(m.az*180/np.pi)
        self.El=float(m.alt*180/np.pi)
        #self.Az=45
        #self.El=10
        if self.El < 0:
            self.lblInfoTxt.setText('Månen är under horisonten')
            self.lblInfoTxt.setStyleSheet("background-color: yellow ; color = red;" )
        else:
            self.lblInfoTxt.setText(self.infoTxt)
            self.lblInfoTxt.setStyleSheet("background-color: white ; color = red;" )
        self.lblMoonAzimuth.setText(f'{self.Az:.1f}')
        self.lblMoonElevation.setText(f'{self.El:.1f}')
              

    
    """ *************************************************************************************************************************
                                                    D I S P L A Y     C O M P A S S
    ************************************************************************************************************************* """ 
    
    
            
    def paintEvent(self, event):
        
        """
        secondHand = QPolygon([
            QPoint(7, 8),
            QPoint(-7, 8),
            QPoint(0, -80)
        ])
        
        textColor = QColor(150, 0, 150)
        hourColor = QColor(127, 0, 127)
        minuteColor = QColor(0, 100, 250, 200)
        secondColor = QColor(195, 0, 0, 150)
        pen = QPen(QColor(50,25,30))
        """
        painter = QPainter(self)
        #painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.drawCompass(painter,self.compass_gradtal, self.elevation_gradtal)
        #self.drawElevation(painter,self.compass_gradtal)
        #painter.end()
        
    def drawCompass(self, painter, degrees, degrees_elevation):    
             
        
        
        pen = QPen()
        degr=[90, 120, 150, 180, 210, 240 , 270, 300, 330, 0, 30, 60, ]
        for i in degr:                    #Skapar Urtavla timmar
            if i == 0:
                x=int(550+150*np.cos((i-90)*np.pi/180))
                y=int(175+150*np.sin((i-90)*np.pi/180))
                painter.drawText(QPoint(x, y), str(i))
            else:    
                x=int(550+150*np.cos((i-90)*np.pi/180))
                y=int(175+150*np.sin((i-90)*np.pi/180))
                painter.drawText(QPoint(x, y), str(i))
        
        
        #painter.translate(self.width() / 2, self.height() / 2)
        #painter.scale(side / 200, side / 200)

        painter.setPen(QColor(127, 0, 127))
        painter.translate(555, 173)
        for i in range(12):                           #Skapar Urtavla timmar
            painter.drawLine(125, 0, 133, 0)
            painter.rotate(30.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 100, 250, 200))
        #painter.save()
        #painter.restore()

        painter.setPen(QColor(0, 100, 250, 200)) 
        for j in range(60):                           #Skapar Urtavla minuter
            if (j % 5) != 0:
                painter.drawLine(125, 0, 133, 0)
            painter.rotate(6.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(195, 0, 0, 150))
        painter.save()
        painter.restore()

        painter.rotate(degrees)  
        painter.drawConvexPolygon(QPolygon([
            QPoint(7, 8),
            QPoint(-7, 8),
            QPoint(0, -125)]))
        painter.rotate(-degrees) 
        painter.setPen(QColor(0, 100, 250, 200)) 
        
        painter.rotate(270+degrees_elevation)
        painter.drawLine(0, 0, 133, 0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(195, 0, 0, 150))


        painter.setBrush(QColor(0, 100, 250, 200))
        painter.save()
        painter.restore()

    def drawElevation(self, painter, degrees):
        pen = QPen()
        degr=[90, 120, 150, 180, 210, 240 , 270, 300, 330, 0, 30, 60, ]
        #painter.translate(500, 173)
        for i in degr:                    #Skapar Urtavla timmar
            if i == 0:
                x=int(600+150*np.cos((i-90)*np.pi/180))
                y=int(173+150*np.sin((i-90)*np.pi/180))
                painter.drawText(QPoint(x, y), str(i))
            else:    
                x=int(600+150*np.cos((i-90)*np.pi/180))
                y=int(173+150*np.sin((i-90)*np.pi/180))
                painter.drawText(QPoint(x, y), str(i))
        
        
        #painter.translate(self.width() / 2, self.height() / 2)
        #painter.scale(side / 200, side / 200)

        painter.setPen(QColor(127, 0, 127))
        painter.translate(100, 100)
        for i in range(12):                           #Skapar Urtavla timmar
            painter.drawLine(125, 0, 133, 0)
            painter.rotate(30.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 100, 250, 200))
        #painter.save()
        #painter.restore()

        painter.setPen(QColor(0, 100, 250, 200)) 
        for j in range(60):                           #Skapar Urtavla minuter
            if (j % 5) != 0:
                painter.drawLine(125, 0, 133, 0)
            painter.rotate(6.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(195, 0, 0, 150))
        painter.save()
        painter.restore()

        painter.rotate(degrees)  
        painter.drawConvexPolygon(QPolygon([
            QPoint(7, 8),
            QPoint(-7, 8),
            QPoint(0, -125)]))
       
        
        painter.setBrush(QColor(0, 100, 250, 200))
        painter.save()
        painter.restore()
    

if __name__ == '__main__':

    app = QApplication(sys.argv)
    demo = MyApp()
    demo.show()
    sys.exit(app.exec_())
    
