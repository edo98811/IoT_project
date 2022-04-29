from email import message
import random
from MyMQTT import *
from MQTT import *
import requests
import json 
import time



class sensor_def():                                                     ### definisce un nuovo sensore
    def __init__(self, sensor_type, sensor_ID, range, unit ):
        self.sensor_type = sensor_type
        self.sensor_ID = sensor_ID
        self.range = range # lista di due numeri
        self.unit = unit

    # genera un numero casuale nel range impostato (self.range)
    def get_reading(self):                                          
        output = random.randint(self.range[0],self.range[1])
        return output



class device_connector():                                                 #classe del device connector (publisher MQTT)
    def __init__(self, broker, port, patient_ID, topic,catalog_address):

        self.dc = MQTT(patient_ID, broker, port, self)
        self.topic = topic

        # avvia la connessione MQTT
        self.dc.start()
        self.basetime = time.time() 

        # template messaggio publisher
        self._message = {			
            'p_ID':patient_ID,
            't':self.basetime,
            'e':[],
            'latitude':0,
            'longitude':0
			}

        #inizializza una lista vuota in cui andrà a mettere gli oggetti sensore
        self._sensors = []

        #prende dal catalog i sensori assegnati a questo device connector 
        sensors = json.loads(requests.get(catalog_address + '/get_sensors',params= {'p_ID':patient_ID}).text)#chiede la lista dei sensori del patient id che gli passo  

        # riceve un messaggio di questo tipo:
                    # sensors = {
                    #    'sl': [
                    #       {
                    #     "is_critical":s_info["is_critical"],
                    #     "safe_range":s_info["safe_range"],
                    #     "type_ID":s_type["type_ID"],
                    #     "type":s_type["type"],
                    #     "range":s_type["range"],
                    #     "unit":s_type["unit"]
                    #       },
                    # ...
                    #    ]
                    # }


        #itera nella lista sl del messaggio ricevuto
        for sensor in sensors['sl']:

            # utilizzando la classe sensor_def definisce i sensori associati al device connector
            sensor = sensor_def(sensor['sensor_type'],sensor['sensor_ID'],sensor['range'],sensor['unit'])
            self._sensors.append(sensor)

            # template messaggio del sensore        
            self._message['e'].append({                            
                'n':sensor.sensor_ID,
                'vs':sensor.sensor_type,
                'v':'',
                'u':sensor.unit,
                'is_critical':sensor.is_critical, 
                'safe_range':sensor.critical_range
            })
        
    # prende il valore del sensore e lo inserisce nel messaggio 
    def get_readings(self): 

        for n,sensor in enumerate(self._sensors):

            value = sensor.get_reading() #
            self.message = self._message # copia il template 
            self.message['e'][n]['v'] = value

        print("sensori funzionanti")
        self.message['t'] = time.time()-self.basetime 

        # genera una posizione casuale vicina a quella attuale
        # latitudine e longitudine modificati casualmente
        self.message['latitude'] = self.message['latitude'] + random.randint(-10,+10) # ipotizzando che la posizione vari casualmente di questa quantità
        self.message['longitude'] = self.message['latitude'] + random.randint(-10,+10)

    
    #pubblica il messaggio scritto in get_readings
    def send(self):

        self.dc.my_publish(self.topic, self.message) #pubblica nel topic corretto poi cancella il messaggio 
        del self.message # elimina il messaggio dopo averlo mandato
        # il messaggio dovrebbe essere ricevuto dal data analysis

    # template messaggio inviato: 
                # message = {			
                # 'p_ID':patient_ID,
                # 't':basetime,
                # 'e':[ misurazioni
                #         {               
                #         'n':sensor_ID,
                #         'vs':sensor_type,
                #         'v':'',
                #         't':time,
                #         'u':unit
                #         'iscritical':
                #         'saferange':
                #         },
                #         {               
                #         'n':sensor_ID,
                #         'vs':sensor_type,
                #         'v':'',
                #         't':time,
                #         'u':unit,
                #         'iscritical':
                #         'saferange':
                #         },
                #     ]
                #     'latitude':0,
                #     'longitude':0
                # }



if __name__ == '__main__':
    
    catalog_address = 'http://127.0.0.1:8080/catalog_manager'
    patient_ID = 'p_1'

    # manda una richiesta al catalog per i dati della connessione MQTT del device connector
    pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,params= {"p_ID":patient_ID}).text)
    print(pat_info)
    device_connector1 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"],catalog_address)

    # per simulare un sistema più complesso viene inizializzato un secondo device connector che funzinerà in parallelo al primo 
    patient_ID = 'p_2'
    pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,params = {"p_ID":patient_ID}).text)
    print(pat_info)
    device_connector2 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"], catalog_address)

    while True:
        time.sleep(10)
        device_connector1.get_readings()
        device_connector1.send()
        device_connector2.get_readings()
        device_connector2.send()

 
