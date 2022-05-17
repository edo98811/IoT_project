from MyMQTT import *
import requests
import pprint
#import schedule
import time

class WK_Report:
    def __init__(self, broker, port, topic, catalog_address, url):
        self.catalog_address = catalog_address
        self.client = MyMQTT("WK_Report",broker,port,self)
        self.client.start()
        self.topic = topic
        
        self._url = url  


    def weekly_report(self):
        # template url per i vari chart
        # https://api.thingspeak.com/channels/<CH_id>/charts/<field_id>?days=7       

        # template messaggio di cui fare il publish per il telegram bot
        # {
        #   pat_full_name = ''
        #   doc_chat_id = ''
        #   url_chart = ''
        # }


        patients = json.loads(requests.get(self.catalog_address + '/get_patients').text)
        
        # Definisce l'url 
        for pat in patients:

            newUrl = self._url 
            uri = newUrl.split('/')
            uri[-3] = str(pat['TS_chID']) 
            # COME FARE PER QUANDO HO PIU' SENSORI E QUINDI PIU' URL PER PAZIENTE
            newUrl = '/'.join(uri)
            msg = {
                "fullName":[f"{pat['personal_info']['name']} {pat['personal_info']['surname']}" ],
                "docID":[pat['doctor_ID']],
                "url_chart": [newUrl]
            }

        # messaggio mandato al medico 
       
        self.weekly_report.myPublish(self.topic, msg)



if __name__ == "__main__":

    ####       CODICE DI "DEBUG"                                                        # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("../Catalog/catalog.json",'r') as f:                                              # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat['base_port']
    catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]
    ####

    #with open("config.json",'r') as f:
    #    catalog_address = json.load(f)["catalog_address"]

    # Ottiene dal catalog l'indirizzo del servizio MQTT
    MQTT_info = json.loads(requests.get(catalog_address+"/get_service_info", params =  {'service_ID':'MQTT'}).text)
    broker = MQTT_info["broker"]
    port = MQTT_info["port"]
    base_Topic= MQTT_info["baseTopic"]

    # creo lista di topic a cui il telebot fa da subscriber
    topic =  [base_Topic + json.loads(requests.get(catalog_address+"/get_service_info", params =  {'service_ID':'weekly_report'}).text)["topic"]]

    # ricerca dell'url a cui si farà la richiesta di get per avere i dati di ogni settimana
    url = json.loads(requests.get(catalog_address+"/get_service_info", params =  {'service_ID':'Thingspeak'}).text)["url_weekly_report"]

    wkr = WK_Report(broker,port, topic, catalog_address, url)
    #schedule.every().monday.at("9:00").do(wkr.weekly_report)
    wkr.weekly_report()

    print("Weekly Report started ...")
    while True:
        time.sleep(3)
