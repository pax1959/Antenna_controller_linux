# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 15:03:00 2022

@author: peter
"""

import csv

with open("COM-port.csv",'r') as file_3:               #Elevering: Läs in tabell med puls <-> grader
    csv_reader = csv.reader(file_3, delimiter=';')        
    for rad in csv_reader:
        print(rad[0])

portNr='COM10'

with open ("COM-port.csv",'w',newline="") as file:
    csv_writer=csv.writer(file,delimiter=";")
    csv_writer.writerow([portNr])
    
class Window_1():
    def __init__(self):
        self.var_1='Peter'
    
    def print_out():
        print('Hello world')

Window_1.print_out()
