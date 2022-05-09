from email import message
import random
from MyMQTT import *
from MQTT import *
import requests
import json 
import time
from copy import deepcopy


class sensor_def():             ### definisce un nuovo sensore
    def __init__(self, sensor_type, sensor_ID, catalog_address):
        self.sensor_type = sensor_type
        self.sensor_ID = sensor_ID
        self.range = json.loads(requests.get(catalog_address+"/sensor-general-info",params={"type": sensor_type}).text)["range"]

    # genera un numero casuale nel range impostato (self.range)
    def get_reading(self):                                          
        output = random.randint(self.range[0],self.range[1])
        return output



class device_connector():       ### classe del device connector (publisher MQTT)
    def __init__(self, broker, port, patient_ID, topic, catalog_address):

        # avvia la connessione MQTT
        self.dc = MQTT(patient_ID, broker, port, self)
        self.dc.start()

        self.topic = topic        
        self.basetime = time.time() 

        # template messaggio pubblicato dal DC
        self._message = {			
            'bn': patient_ID,       #basename
            'bt': self.basetime,    #basetime
            'e': [],                #event objects array
            'latitude': 0,       
            'longitude': 0          #position data
			}

        #inizializza una lista vuota in cui andrà a mettere gli oggetti sensore
        self._sensors = []

        #prende dal catalog i sensori assegnati a questo device connector 
        sensors = json.loads(requests.get(catalog_address + '/get_sensors',params= {'p_ID':patient_ID}).text) #chiede la lista dei sensori del patient id che gli passo  

            # sensors = [{
            #       "type": sensor["sensor_type"],
            #       "ID": sensor["sensor_ID"]
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
            s = sensor_def(sensor['type'],sensor['ID'],catalog_address)
            self._sensors.append(s)

            # template messaggio del sensore        
            self._message['e'].append({                            
                'n': s.sensor_ID,       #resource name
                'vs': s.sensor_type,    #buh type_ID
                'v': 0,                 #value
                't': 0,                 #timestamp
                'u': json.loads(requests.get(catalog_address+"/sensor-general-info", params={"type":s.sensor_type}).text)["unit"]
            })                          #unit
        

        ## DA CONTROLLARE
    # prende il valore del sensore e lo inserisce nel messaggio 
    def get_readings(self): 

        for n,sensor in enumerate(self._sensors):

            value = sensor.get_reading() #
            self.message = deepcopy(self._message) # copia il template 
            self.message['e'][n]['v'] = value
            self.message['e'][n]['t'] = time.time()-self.basetime 

        print("sensori funzionanti")
        
        # genera una posizione casuale vicina a quella attuale
        # latitudine e longitudine modificati casualmente
        self.message['latitude'] = self.message['latitude'] + random.randint(-10,+10) # ipotizzando che la posizione vari casualmente di questa quantità
        self.message['longitude'] = self.message['latitude'] + random.randint(-10,+10)


        ## DA CONTROLLARE
    #pubblica il messaggio scritto in get_readings
    def send(self):

        self.dc.my_publish(self.topic, self.message) #pubblica nel topic corretto poi cancella il messaggio 
        
        del self.message # elimina il messaggio dopo averlo mandato
        
        # il messaggio dovrebbe essere ricevuto dal data analysis


#################################################################################################


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

    # manda una richiesta al catalog per i dati della connessione MQTT del device connector
    pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,params= {"p_ID":patient_ID}).text)
            # msg = {
            #             "broker":catalog["services"]["MQTT"]["broker"],
            #             "port":catalog["services"]["MQTT"]["port"],
            #             "topic":pat["device_connector"]["topic"],
            #         }
    
    # Definizione del DC_1
    device_connector1 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"],catalog_address)
    

    # # per simulare un sistema più complesso viene inizializzato un secondo device connector che funzinerà in parallelo al primo 
    # patient_ID = 'p_2'
    # pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,params = {"p_ID":patient_ID}).text)
    # print(pat_info)
    # device_connector2 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"], catalog_address)

    while True:
        time.sleep(16)
        device_connector1.get_readings()
        device_connector1.send()
        # device_connector2.get_readings()
        # device_connector2.send()

 
