from email import message
import random
from MyMQTT import *
from MQTT import *
import requests
import json 
import time



class sensor_def():                                                     ### definisce un nuovo sensore
    def __init__(self, sensor_type, sensor_ID, range, safe_range, unit):
        self.sensor_type = sensor_type
        self.sensor_ID = sensor_ID
        self.range = range
        self.safe_range = safe_range
        self.unit = unit
        
    # genera un numero casuale nel range impostato (self.range)
    def get_reading_safe(self):                                          
        output = random.randint(self.safe_range[0],self.safe_range[1])
        return output

    ### serve a noi per simulare una lettura fuori range -> 
            # funziona cosi
            # range -> [min safe_min safe_max max]
            # se voglio generarare un numero fuori dal range "sicuro" lo genero tra safe_max e max, quindi all'interno 
            # dell'intervallo di funzionamento del sensore ma fuori dal range di sicurezza 

    def get_reading_alert(self):   
        try:                                     
            output = random.randint(self.safe_range[1],self.range[1])
        except:
            output = random.randint(self.safe_range[0],self.safe_range[1])
        return output
    


class device_connector():                                                 #classe del device connector (publisher MQTT)
    def __init__(self, broker, port, patient_ID, topic, catalog_address):

        # avvia la connessione MQTT
        self.dc = MyMQTT(patient_ID, broker, port, self)
        self.dc.start()
        self.critical = 0
        self.topic = topic   
        self.basetime = time.time() 

        # template messaggio pubblicato dal DC
        self._message = {			
            'bn':patient_ID,
            't':self.basetime,
            'e':[],
            'location':{
                'latitude':0,
                'longitude':0
            }
			}
        self._message['e'].append({                          
                'n':'lat',
                'v':0,
            })
        self._message['e'].append({                            
                'n':'lon',
                'v':0,
            })

        #inizializza una lista vuota in cui andrà a mettere gli oggetti sensore
        self._sensors = []

        #prende dal catalog i sensori assegnati a questo device connector 
        sensors = json.loads(requests.get(catalog_address + '/get_sensors',params= {'patient_ID':patient_ID}).text) #chiede la lista dei sensori del patient id che gli passo  

                                # sensors = [{
                                #       "type": sensor["sensor_type"],
                                #       "ID": sensor["sensor_ID"]
                                #       "range"
                                #       "safe_range"    
                                #       "unit"
                                #   },
                                #   ... ,
                                #   {
                                #       "type": sensor["sensor_type"],
                                #       "ID": sensor["sensor_ID"]
                                #   }
                                # ]


        # itera nella lista sl del messaggio ricevuto
        for sensor in sensors:

            # utilizzando la classe sensor_def definisce i sensori associati al device connector
            s = sensor_def(sensor['type_ID'],sensor['type'],sensor["range"], sensor["safe_range"], sensor["unit"])
            self._sensors.append(s)

            # template messaggio del sensore        
            self._message['e'].append({                            
                'n':s.sensor_type,
                'v':'',#value
                'u':s.unit
            })
        
    # prende il valore del sensore e lo inserisce nel messaggio 
    def get_readings(self): 

        for n,sensor in enumerate(self._sensors):
            if self.critical == 0:
                value = sensor.get_reading_safe() #
            if self.critical == 1: 
                value = sensor.get_reading_critical() #
            self.message = self._message # copia il template 
            self.message['e'][n]['v'] = value

        print("sensori funzionanti")
        self.message['t'] = time.time()-self.basetime 

        # genera una posizione casuale vicina a quella attuale
        # latitudine e longitudine modificati casualmente
        self.message['location']['latitude'] = self.message['location']['latitude'] + random.randint(-10,+10) # ipotizzando che la posizione vari casualmente di questa quantità
        self.message['location']['longitude'] = self.message['location']['latitude'] + random.randint(-10,+10)

    # cambia lo stato di criticità delle letture che arrivano dal device connector 
    def change(self):
     if self.critical==0:
        self.critical=1
     else:      
        self.critical==0

    #pubblica il messaggio scritto in get_readings
    def send(self):

        self.dc.myPublish(self.topic, self.message) #pubblica nel topic corretto poi cancella il messaggio 
        del self.message # elimina il messaggio dopo averlo mandato
        # il messaggio dovrebbe essere ricevuto dal data analysis

        # template messaggio inviato: 
                                # message = {			
                                # 'patient_ID':patient_ID,
                                # 't':basetime,
                                # 'e':[ 
                                #         'n':lat e lon,
                                #         'v':'',
                                #         },
                                #         .... dal secondo elemento della lista in poi ci sono i sensori
                                #       {               
                                #         'n':sensor_type,
                                #         'v':'',
                                #         'u':unit,
                                #         },
                                #         {               
                                #         'n':sensor_type,
                                #         'v':'',
                                #         'u':unit,
                                #         },



if __name__ == '__main__':
    
####       CODICE DI "DEBUG"                                                            # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("./catalog.json",'r') as f:                                               # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]
####

    # Di default il DC sa a quale paziente è associato, dunzue il patient_ID è definito all'interno del suo codice
    patient_ID = 'p_1'
    print(catalog_address)
    # manda una richiesta al catalog per i dati della connessione MQTT del device connector
    pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,params= {"patient_ID":patient_ID}).text)
    # template messaggio ricevuto dal catalog
                                # msg = {
                                #             "broker":catalog["services"]["MQTT"]["broker"],
                                #             "port":catalog["device_connector"]["port"],
                                #             "topic":pat["device_connector"]["topic"],
                                #         }
    
    # Definizione del DC_1
    device_connector1 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"],catalog_address)
    
    # per simulare un sistema più complesso viene inizializzato un secondo device connector che funzionerà in parallelo al primo 
    patient_ID = 'p_2'
    pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,params = {"patient_ID":patient_ID}).text)
    print(pat_info)
    device_connector2 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"], catalog_address)

    count=30
    while True:
        time.sleep(10)
        print('started')
        count=count-1
        if count==1:
            device_connector1.change()
            device_connector2.change()
        if count==0:
            device_connector1.change()
            device_connector2.change()
            count=30
        device_connector1.get_readings()
        device_connector1.send()
        device_connector2.get_readings()
        device_connector2.send()

