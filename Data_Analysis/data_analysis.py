import json
import time
from MyMQTT import *
import requests as r #da mettere così dappertutto
    
#forse sarebbe meglio chiamarlo data processing

class data_analysis_service():
    def __init__(self, broker, port, service_ID, topic,catalog_address,location_service):
        self.da_service = MyMQTT(( service_ID,broker, port, self))
        self.da_service.start()
        self.da_service.mySubscribe(topic)
        self.catalog_address = catalog_address # tutti gli indirizzi si potrebbero salvare nel catalog e prenderli all'inizio con una richiwsta e poi aggiungere un controllo negli errori nel caso 
        self.location_service = location_service


    def notify(self, topic, msg):

    # template messaggio ricevuto: 
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
        
        msg = json.loads(msg) #in questo caso il messaggio arriva da mqtt quindi in formato stringa

        patient_ID = msg['patient_ID']
        measures = msg['e']

        if measures[0]['n'] == 'lat' & measures[1]['n'] == 'lon':

            msg = {#post_loc
                    "patient_ID":patient_ID,
                    "location": {
                        "latitude":measures[0]['v'],
                        "longitude":measures[1]['v']
                    }
                }
   
        r.post(self.location_service,msg)

            # for n,measure in enumerate(measures):
            #     if measure['n'] =='lon' |  measure['n'] =='lat' #riguardare bene come dovrebbe essere il formato senml
            #         msg = {
            #             "patient_ID":patient_ID,
            #             "sensor_ID":measure['n'],
            #             "location": {
            #                 "latitude":measure['v'][0:4],#potrebbe essere un idea scriverla in questo formato per rispettare senml
            #                 "longitude":measure['v'][5:-1]
            #             }
            #         }
        
            # else: #forse basta proprio anche solo la lettura del dato come in measure, anche sopra, oppure si puo aggiungere anche altre informazioni come il sensore etc
            #     msg = {
            #         "patient_ID":patient_ID,
            #         "sensor_ID":measure['vs'],
            #         "v": measure['v'],
            #         "u":measure["u"]
            #     }
            #     #scrive sul database
            #     #r.post(self.database_address,msg)
            #     print('dati sensosre' + msg["sensor_ID"] + "salvati correttamente")



if __name__ =='__main__':

    ####       CODICE DI "DEBUG"                                                            # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("./catalog.json",'r') as f:                                               # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]
####

    print(catalog_address)
    location_address = r.get(catalog_address +"/get_service_address", params = {'service_ID':'location_service'}).text
    connection_settings = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'data_analysis'}).text)
    mqtt_broker = r.get(catalog_address +"/get_MQTT").text
    
    topic = connection_settings['topic']
    broker = mqtt_broker
    port = connection_settings['port']
    service_ID = connection_settings['service_ID']

    service =  data_analysis_service(broker, port, service_ID, topic, catalog_address, location_address)

    done = False
    while not done:
        #mettere condizione di stop?
        time.sleep(1)