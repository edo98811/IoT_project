from MyMQTT import *
import requests
import time

class WK_Report:
    def __init__(self, broker, port, topic, catalog_address):
        self.catalog_address = catalog_address
        self.client = MyMQTT("WK_Report",broker,port,self)
        self.client.start()
        self.topic = topic
        
        self.url = https://api.thingspeak.com/channels/<channel_id>/feeds.json?days=7   # DA PORTARE NEL CATALOG


        









if __name__ == "__main__":

    ####       CODICE DI "DEBUG"                                                        # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("../catalog.json",'r') as f:                                              # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat['base_port']
    catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]
    ####

    #with open("./config.json",'r') as f:
    #    catalog_address = json.load(f)["catalog_address"]

    # Ottiene dal catalog l'indirizzo del servizio MQTT
    MQTT_info = json.loads(requests.get(catalog_address+"/service-info?name=MQTT").text)
    broker = MQTT_info["broker"]
    port = MQTT_info["port"]

    # creo lista di topic a cui il telebot fa da subscriber
    topic =  json.loads(requests.get(catalog_address+"/service-info?name=weekly_report").text)["topic"] 
    wkr = WK_Report(broker,port, topic, catalog_address)

    print("Weekly Report started ...")
    while True:
        time.sleep(3)
