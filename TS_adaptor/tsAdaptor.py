from MyMQTT import *
import requests
import time
from copy import deepcopy

class TS_Adaptor:
    def __init__(self, broker, port, topic, catalog_address, url):
        self.client = MyMQTT("TS_Adaptor",broker,port,self)
        self.client.start()
        self.topic = topic
        self.client.mySubscribe(self.topic)


        # Templeate del url per la richiesta di POST a TS
        self._url =  url

        # Template del body del POST per TS 
        self._body = {
            "write_api_key": '',
            "updates": []
        }

        # Template del campo 'updates' del body
        self._inUpdates = {
            "created_at": 0
        } # "field<x>": 0  

        {# # template messaggio pubblicato dal DC
        # self._message = {			
        #     'bn': "",               #patientID
        #     'bt': 0,                #basetime
        #     'e': [],                #event objects array
        #     'latitude': 0,       
        #     'longitude': 0           #position data
		# 	}

        # # template messaggio del sensore        
        #     self._message['e'].append({                            
        #         'n': s.sensor_ID,       #resource name
        #         'vs': s.sensor_type,    #buh type_ID
        #         'v': 0,                 #value
        #         't': 0,                 #timestamp
        #         'u': json.loads(requests.get(catalog_address+"/sensor-general-info", params={"type":s.sensor_type}).text)["unit"]
        }#     })


    def notify(self,topic,message):
        
        # Converte il messaggio in formato json
        message = json.loads(message)

        # Ottiene il json del paziente da cui arriva il messaggio
        dc = int(topic.split('_')[-1])-1
        pat = json.loads(requests.get(catalog_address+'/get_patients').text)[dc]

        # Definisce l'url a cui mandare la richiesta POST
        newUrl = self._url 
        uri = newUrl.split('/')
        uri[-2] = str(pat['TS_chID'])
        newUrl = '/'.join(uri)

        # Definizione del body
        body = deepcopy(self._body)
        body['write_api_key'] = pat['TS_wKey']

        inUpdates = deepcopy(self._inUpdates)
        bt = message['bt']
        inUpdates['created_at'] = str(bt + message['e'][0]['t']).split('.')[0]

        for s in message['e']:
            i = s['n'].split('_')[-1]
            exec(f"inUpdates['field{i}'] = {s['v']}")

        body['updates'].append(inUpdates)

        # Inoltra la richiesta di POST
        requests.post(newUrl,json=body)

##################################################################################################

if __name__ == "__main__":

    ####       CODICE DI "DEBUG"                                                            # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("../Catalog/catalog.json",'r') as f:                                                  # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                                  # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                                 # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]
    ####

    # Ottiene informazioni per la connessione MQTT
    mqtt = json.loads(requests.get(catalog_address+"/get_service_info",params =  {'service_ID':'MQTT'}).text)
    broker = mqtt['broker']
    port = mqtt['port']

    # Topic
    base_Topic= mqtt["baseTopic"]
    topic = f"{base_Topic}/{json.loads(requests.get(catalog_address+'/get_service_info',params =  {'service_ID':'ThingSpeak'}).text)['topic']}"
    
    # URL
    url = json.loads(requests.get(catalog_address+"/get_service_info",params =  {'service_ID':'ThingSpeak'}).text)["url_update"] 

    # Inizializza oggetto TS_Adaptor
    tsa = TS_Adaptor(broker, port, topic, catalog_address, url)

    print("Adaptor started...")

    while True:
        time.sleep(3)
        print('.')

