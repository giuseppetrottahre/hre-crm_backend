import xml.etree.ElementTree as ET
import math
import pandas 
import sys
from xml.dom import minidom

'''
R	RIPOSO  -> gestita ad ho non inclusa nella tabella di lookup
GIORNATA LAVORATIVA NORMALE -> assieme ad R sono casi base gestiti ad hoc

FE	FERIE
MA	MALATTIA
ST	STRAORDINARIO
NT	TURNO NOTTURNO
RL 	ROL
AL	ALLATTAMENTO
PR	PERMESSI RETRIBUITI
'''

CAUSALI=['FE'
,'MA'
,'ST'
,'NT'
,'RL' 
,'AL'
,'PR'
];

def isSpecialDay(dataFrameCellValue):
    for causale in CAUSALI:
        if(str(dataFrameCellValue).startswith(causale)):
            return True
    return False

def getXml(excel_input_file_name):

    excel_data_df = pandas.read_excel(excel_input_file_name, sheet_name='Dati',header=None)
    
    df=excel_data_df.dropna(how='all')
    #informazioni codice azienda, mese (numerico mm), anno (numerico yyyy)
    infoDf=df.head(1)
    CodAziendaUfficiale=infoDf.iat[0,1]
    mese=infoDf.iat[0,3]
    anno=infoDf.iat[0,5]
    #print (infoDf)
    #infomrazioni  calendario
    headerDf=df.iloc[1:3]
    #print(headerDf)
    
    #informazioni dipendenti
    dipendentiDf=df.iloc[3:]
    #print (dipendentiDf)
    
    n_dipendenti=dipendentiDf[0].dropna().count()
    
    fornitura = ET.Element('Fornitura')
    for i in range(n_dipendenti):
        row=4*i
        coddipendenteuff=str(dipendentiDf.iat[row,2])
        dipendente = ET.SubElement(fornitura, 'Dipendente',{"CodAziendaUfficiale":str(CodAziendaUfficiale),"CodDipendenteUfficiale":coddipendenteuff})
        movimenti = ET.SubElement(dipendente, 'Movimenti',{"GenerazioneAutomaticaDaTeorico":"N"})
    
        for j in range(0,31):
            col=5+j
            giorno=headerDf.iat[0,col]
            sgiorno=str(int(giorno)) 
            if giorno<10:
                sgiorno='0'+str(int(giorno))
            smese=str(mese)
            if mese <10: 
                smese='0'+str(mese)
            for k in range(0,3):
                if  pandas.notna(dipendentiDf.iloc[row+k][col]):
                    movimento = ET.SubElement(movimenti, 'Movimento')
                    codGiustificativoUfficiale=ET.SubElement(movimento, 'CodGiustificativoUfficiale')

                    data=ET.SubElement(movimento, 'Data')
                    data.text=str(anno)+'-'+smese+'-'+sgiorno
        
                    if dipendentiDf.iloc[row+k][col]=='R':                         #giornata di riposo
                        codGiustificativoUfficiale.text='01'
                        numore_val='0'
                        numminuti_val='0'
                        giornodiriposo_val='S'
                        giornochiusurastraordinari_val='N'
                    elif isSpecialDay(dipendentiDf.iloc[row+k][col]):
                        specialDayCode=str(dipendentiDf.iloc[row+k][col])[0:2]
                        specialDaylength=str(dipendentiDf.iloc[row+k][col])[2:].replace(',','.')
                        codGiustificativoUfficiale.text=specialDayCode
                        ore_decimal,ore_int=math.modf(float(specialDaylength)) 
                        numore_val=str(int(ore_int))
                        numminuti_val=str(int(ore_decimal*60))
                        giornodiriposo_val='N'
                        giornochiusurastraordinari_val='N'
                        
                    elif dipendentiDf.iloc[row+k][col]:                        #giornata lavorativo normale
                #        dipendentiDfWithNotNa=dipendentiDf.iloc[row+k].fillna(0,inplace=True)
                        codGiustificativoUfficiale.text='01'
                        ore_decimal,ore_int=math.modf(dipendentiDf.iat[0,col]) 
                        numore_val=str(int(ore_int))
                        numminuti_val=str(int(ore_decimal*60))
                        giornodiriposo_val='N'
                        giornochiusurastraordinari_val='N'
                    else:
                        print("Caso non gestito")
                    numore=ET.SubElement(movimento, 'NumOre')
                    numore.text=numore_val
                    numminuti=ET.SubElement(movimento,'NumMinuti')
                    numminuti.text=numminuti_val
                    numincentesimi= ET.SubElement(movimento,'NumMinutiInCentesimi') 
                    numincentesimi.text=str(round(int(numminuti_val)*100/60))
                    giornodiriposo=ET.SubElement(movimento,'GiornoDiRiposo')
                    giornodiriposo.text=giornodiriposo_val
                    giornochiusurastraordinari=ET.SubElement(movimento,'GiornoChiusuraStraordinari')
                    giornochiusurastraordinari.text=giornochiusurastraordinari_val
    
            
    #ET.indent(fornitura, space="\t", level=0)
    #ET.dump(fornitura)
    tree = ET.ElementTree(fornitura)
    #tree.write(excel_input_file_name+'.xml')


    xmlstr = minidom.parseString(ET.tostring(fornitura)).toprettyxml(indent="   ")
    with open(excel_input_file_name+'.xml', "w") as f:
        f.write(xmlstr)
    return excel_input_file_name+'.xml' 
    
if __name__ == "__main__":
    getXml(sys.argv[1]);

