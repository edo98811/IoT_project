# senza safe range e cambio di stato
from copy import deepcopy
import random
from MyMQTT import *
import requests
import json 
import time



class sensor_def():                                                     ### definisce un nuovo sensore
    def __init__(self, sensor_type, sensor_type_ID, range, safe_range, unit):
        self.sensor_type = sensor_type
        self.sensor_type_ID = sensor_type_ID
        self.range = range
        self.safe_range = safe_range
        self.unit = unit
        
    # genera un numero casuale nel range impostato (self.range)
    def get_reading_safe(self):                                          
        value =  random.randint(self.safe_range[0],self.safe_range[1])
        #print (value)
        return value

    ### serve a noi per simulare una lettura fuori range -> 
            # funziona cosi
            # range -> [min safe_min safe_max max]
            # se voglio generarare un numero fuori dal range "sicuro" lo genero tra safe_max e max, quindi all'interno 
            # dell'intervallo di funzionamento del sensore ma fuori dal range di sicurezza 

    def get_reading_alert(self):   
        try:      
            # genera un segnale fuori dal range solo se il range effetivamente esiste (non se è 0 e 0)                            
            return random.randint(self.safe_range[1],self.range[1])
        except:
            return random.randint(self.safe_range[0],self.safe_range[1])

    


class device_connector():                                               ###classe del device connector (publisher MQTT)
    def __init__(self, broker, port, patient_ID, topic, catalog_address):

        # avvia la connessione MQTT
        self.dc = MyMQTT(patient_ID, broker, int(port), self)
        self.dc.start()
        self.critical = 0
        self.topic = topic   
        self.basetime = time.time() 

        # template messaggio pubblicato dal DC
        self._message = {			
            'bn':patient_ID,
            'bt':self.basetime,
            't':0,
            'e':[]
			}
        self._message['e'].append({                          
                'n':'lat',
                'v': random.uniform(45.0000, 45.1000),
            })
        self._message['e'].append({                            
                'n':'lon',
                'v': random.uniform(7.5000, 7.8400),
            })
        #inizializza una lista vuota in cui andrà a mettere gli oggetti sensore
        self._sensors = []

        #prende dal catalog i sensori assegnati a questo device connector 
        sensors = json.loads(requests.get(catalog_address + '/get_sensors',params= {'patient_ID':patient_ID}).text) #chiede la lista dei sensori del patient id che gli passo  
       #print(json.dumps(sensors))
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
        # print(self._message)
        
    # prende il valore del sensore e lo inserisce nel messaggio 
    def get_readings(self): 
        print("\nGetting readings...")
        self.message = deepcopy(self._message)
        # genera una posizione casuale vicina a quella attuale, latitudine e longitudine vengono modificati casualmente
        self.message['e'][0]['v'] = self.message['e'][0]['v'] + random.randint(-10, 10)*0.0001 # ipotizzando che la posizione vari casualmente di questa quantità
        self.message['e'][1]['v'] = self.message['e'][1]['v'] + random.randint(-10, 10)*0.0001 

        # itera su tutti i sensori memorizzati e aggiorna il contenuto dei campi del message, poi lo manda
        for n,sensor in enumerate(self._sensors):
            
            if self.critical == 0:
                value = sensor.get_reading_safe() 
            elif self.critical == 1: 
                value = sensor.get_reading_alert()

            self.message['e'][n+2]['v'] = value
            print(f"Sensor type: {self.message['e'][n+2]['n']}   -   Value: {value} {self.message['e'][n+2]['u']}")
            
        self.message['t'] = time.time()-self.basetime 
        
    # cambia lo stato di criticità delle letture che arrivano dal device connector (per debug)
    def change(self):
     if self.critical==0:
        self.critical=1
     else:      
        self.critical=0

    #pubblica il messaggio scritto in get_readings
    def send(self):

        ################# debug 
        if self.critical:
            print("Device connector sending values out of safe range")
        #########################

        
        self.dc.myPublish(self.topic, self.message) #pubblica nel topic corretto poi cancella il messaggio 
        del self.message # elimina il messaggio dopo averlo mandato
        # il messaggio dovrebbe essere ricevuto dal data analysis

        print("Message sent!")

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
                                #       },
                                #       {               
                                #         'n':sensor_type,
                                #         'v':'',
                                #         'u':unit,
                                #         },



if __name__ == '__main__':
    
####                                                               
    with open("config.json",'r') as f:                                               
        cat = json.load(f)                                                              
    host = cat["base_host"]                                                            
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["address"]
####

    # Di default il DC sa a quale paziente è associato, dunzue il patient_ID è definito all'interno del suo codice
    patient_ID = 'p_1'
    # manda una richiesta al catalog per i dati della connessione MQTT del device connector
    patient_info  = json.loads(requests.get(catalog_address + '/get_dc_info' , params= {"patient_ID":patient_ID}).text)
    # template messaggio ricevuto dal catalog
                                # msg = {
                                #             "broker":catalog["services"]["MQTT"]["broker"],
                                #             "port":catalog["device_connector"]["port"],
                                #             "topic":pat["device_connector"]["topic"],
                                #         }
    
    # Definizione del DC_1
    device_connector1 = device_connector(patient_info ["broker"], patient_info ["port"], patient_ID, patient_info["topic"],catalog_address)
    print(f"Publishing on topic: {patient_info['topic']}")
    #  # per simulare un sistema più complesso viene inizializzato un secondo device connector che funzionerà in parallelo al primo 
    # patient_ID = 'p_2'
    # patient_info  = json.loads(requests.get(catalog_address + '/get_dc_info' ,params = {"patient_ID":patient_ID}).text)
    # print(patient_info )
    # device_connector2 = device_connector(patient_info ["broker"], patient_info ["port"], patient_ID, patient_info ["topic"], catalog_address)

    count=7
    while True:
        time.sleep(5)
        # print(count)
        count=count-1
        if count==1:
            device_connector1.change()
            #device_connector2.change()
        if count==0:
            device_connector1.change()
            #device_connector2.change()
            count=7
        device_connector1.get_readings()
        device_connector1.send()
        #device_connector2.get_readings()
        #device_connector2.send()

