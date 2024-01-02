import numpy as np
import matplotlib.pyplot as plt
import ephem
import csv
import datetime
import pandas as pd
import serial


#returnerar aktuellt Az och El värde för solen och månen
# moon_sun=0 --> returnerar Az El från månen
# moon_sun=1 --> returnerar Az El från solen
def Az_El_date_time(moon_sun):   
    now=datetime.datetime.utcnow()
    g = ephem.Observer()    
    g.long=ephem.degrees('12.54089')    #longitud JO67gw 
    g.lat=ephem.degrees('57.92943')     #latitud JO67gw
    t=datetime.datetime(now.year,now.month,now.day,now.hour,now.minute)
    g.date = t.strftime('%Y/%m/%d %H:%M')   
    if moon_sun==0:
        m = ephem.Moon()
    if moon_sun==1:   
        m = ephem.Sun()    
    m.compute(g)    
    Az=float(m.az*180/np.pi)
    El=float(m.alt*180/np.pi)
    return (Az,El)


#Ny mätning 2023-02-27 efter att ha uppdaterat Az-rotorindikatorn med dubbla varv.

# 118 grader är vid pinne nedtryckt i marken vid svart vinbärsbuske.
# 169 är vid pinnen som är nedstucken 98 cm i slänten, 89 cm från bakersta cementplattaraden.
# 216 grader cementplatta hörnet stupränna - vägg carport.
# 290 grader är i hörnet av cementplattorna närmast flaggstången.


df_degr_ADC=pd.DataFrame(np.array([[ 36, 110, 118, 130, 141, 169, 216, 290], 
                                   [241, 358, 371, 392, 405, 445, 512, 603]]).transpose(), 
                                    columns=['degr','ADC'])
deg = 2           
coeff=np.polyfit(df_degr_ADC['degr'], df_degr_ADC['ADC'], deg)



degr_0_360 =pd.Series([x  for x in np.arange(0,361,0.5)])
ADC_to_CSV=pd.Series([round(coeff[deg-2]*x**2 +coeff[deg-1]*x+coeff[deg]) for x in degr_0_360])
df_ADC=pd.concat([degr_0_360, ADC_to_CSV],axis='columns')

#-----------------------   Aktuell ADC_to_grader_tabell 2023-02-27 kl. 21.30:   ---------------------------

df_ADC.to_csv("ADC_to_grader_tabell_2023-03-26.csv", sep=';', header=False, index=False)  

#----------------------------------------------------------------------------------------------------------

plt.figure()
plt.plot(degr_0_360, ADC_to_CSV)
plt.plot(df_degr_ADC['degr'],df_degr_ADC['ADC'], 'ro')
plt.show()

print('AZ_El_Now=',Az_El_date_time(0))

print('Ready...')