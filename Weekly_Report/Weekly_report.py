from MyMQTT import *
import requests
import pprint
from schedule import repeat, every, run_pending
import time
from copy import deepcopy

class WK_Report:
    def __init__(self, broker, port, topic, catalog_address, url):
        self.catalog_address = catalog_address
        self.client = MyMQTT("WK_Report",broker,port,self)
        self.client.start()
        self.topic = topic
        
        self._url = url  
        self._msg = {
            'chat_ID': ... ,
            'full_name': ... ,
            'sensors' : [ ... ],
            'urls' : [ ... ]
                  }


    def weekly_report(self):
        # template url per i vari chart
        # https://api.thingspeak.com/channels/<CH_id>/charts/<field_id>?days=7       

        # template messaggio di cui fare il publish per il telegram bot
        # {
        #   pat_full_name = ''
        #   doc_chat_id = ''
        #   url_chart = ''
        # }

        print('Sending weekly reports...')
        patients = json.loads(requests.get(self.catalog_address + '/get_patients').text)
        docs = json.loads(requests.get(f"{self.catalog_address}/avail_docs").text)
        # Definisce l'url 
        for pat in patients:
            print('...')

            msg = deepcopy(self._msg) 
            msg['chat_ID'] = docs['chatID'][docs['docID'].index(pat['doctor_ID'])]
            msg['full_name'] = f"{pat['personal_info']['name']} {pat['personal_info']['surname']}"

            avail_sens = json.loads(requests.get(f"{catalog_address}/avail_devs").text)

            msg['sensors'] = [avail_sens['fullName'][avail_sens['devID'].index(s['type_ID'])] for s in pat['sensors']]
            chID = pat['TS_chID']
            msg['urls'] = [eval(f"f'{self._url}'") for i,chID in zip(range(1,len(msg['sensors'])+1),[pat['TS_chID']]*len(msg['sensors']))]

            self.client.myPublish(self.topic, msg)

        print('All reports succesfully sent!')


if __name__ == "__main__":

    ####       CODICE DI "DEBUG"                                                        # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("config.json",'r') as f:                                              # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat['base_port']
    catalog_address = "http://"+host+":"+port+cat["address"]
    ####

    # Ottiene dal catalog l'indirizzo del servizio MQTT
    MQTT_info = json.loads(requests.get(catalog_address+"/get_service_info", params =  {'service_ID':'MQTT'}).text)
    broker = MQTT_info["broker"]
    port = MQTT_info["port"]
    base_Topic= MQTT_info["baseTopic"]

    # creo lista di topic a cui il telebot fa da subscriber
    topic =  base_Topic + '/' + json.loads(requests.get(catalog_address+"/get_service_info", params =  {'service_ID':'telegram_bot'}).text)["weekly_report_topic"]

    # ricerca dell'url a cui si farà la richiesta di get per avere i dati di ogni settimana
    url = json.loads(requests.get(catalog_address+"/get_service_info", params =  {'service_ID':'ThingSpeak'}).text)["url_weekly_report"]

    wkr = WK_Report(broker,port, topic, catalog_address, url)
    time.sleep(3)

    #### Scommentare per passare alla programmazione settimanale
    # every().monday.at('08:30').do(wkr.weekly_report)
    
    print("Weekly Report started ...")
    # wkr.weekly_report()

    while True:
        #### Scommentare per passare alla programmazione settimanale
        # run_pending()
        # time.sleep(3)
        pass
