from MyMQTT import *
import requests
import time
from copy import deepcopy
from pprint import pprint

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
        #     't' : 0,                #timestamp
        #     'e': []                #event objects array
		# 	}

        # # template messaggio del sensore        
        #     self._message['e'] = [
        #       {'n': 'lat', 'v': 7}, {'n': 'lon', 'v': 0},
        #       append({                            
        #         'n': s.sensor_type,       #resource name
        #         'v': 0,                 #value
        #         'u': json.loads(requests.get(catalog_address+"/sensor-general-info", params={"type":s.sensor_type}).text)["unit"]
        }#      })


    def notify(self,topic,message):

        print(f"Message from device connector {topic.split('/')[-1]} received:\n")
        
        # Converte il messaggio in formato json
        message = json.loads(message)
        pprint(message)
        print("\n")
        
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
        inUpdates['created_at'] = str(bt + message['t']).split('.')[0]

        fields = [s['type_ID'] for s in pat['sensors']]

        for s in message['e'][2:]:
            i = fields.index(s['n'])+1
            exec(f"inUpdates['field{i}'] = {s['v']}")

        body['updates'].append(inUpdates)

        # Inoltra la richiesta di POST
        resp = requests.post(newUrl,json=body)
        print(f"\n{message['bn']} data updated!")
        for meas in message['e'][2:]:
            print(f"{meas['n']} --> {meas['v']} {meas['u']}")

##################################################################################################

if __name__ == "__main__":

    ####       CODICE DI "DEBUG"                                                            # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("config.json",'r') as f:                                                  # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                                  # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                                 # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["address"]
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
    print("\nAdaptor started...")

    while True:
        time.sleep(3)
        

