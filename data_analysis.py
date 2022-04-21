import json
import time
import MQTT
import requests as r #da mettere così dappertutto
    
#forse sarebbe meglio chiamarlo data processing

class data_analysis_service():
    def __init__(self, broker, port, ID, topic,catalog_address,location_service, database_service):
        self.da_service = MQTT((broker, port, ID, self))
        self.da_service.start()
        self.da_service.my_subscribe(topic)
        self.catalog_address = catalog_address # tutti gli indirizzi si potrebbero salvare nel catalog e prenderli all'inizio con una richiwsta e poi aggiungere un controllo negli errori nel caso 
        self.location_service = location_service
        self.database_address = database_service


    def notify(self, topic, msg):
        
        msg = json.loads(msg) #in questo caso il messaggio arriva da mqtt quindi in formato stringa

        patient_ID = msg['p_ID']
        measures = msg['e']

        for measure in measures:
            if measure['vs'] =='gps': #riguardare bene come dovrebbe essere il formato senml
                msg = {
                    "p_ID":patient_ID,
                    "s_ID":measure['n'],
                    "location": {
                        "latitude":measure['v'][0:4],#potrebbe essere un idea scriverla in questo formato per rispettare senml
                        "longitude":measure['v'][5:-1]
                    }
                }
                r.post(self.location_service,msg) #come funziona post

            else: #forse basta proprio anche solo la lettura del dato come in measure, anche sopra, oppure si puo aggiungere anche altre informazioni come il sensore etc
                msg = {
                    "p_ID":patient_ID,
                    "s_ID":measure['vs'],
                    "v": measure['v'],
                    "u":measure["u"]
                }
                #scrive sul database
                #r.post(self.database_address,msg)
                print('dati sensosre' + msg["s_ID"] + "salvati correttamente")



if __name__ =='__main__':
    dati = json.loads(open('settings_da.json')) # idea -> settings contiene tutte le impostazioni per i microservices in un dizionario 
    topic = dati['topic']
    broker = dati['broker']
    port = dati['port']
    service_ID = dati['service_ID']
    catalog_address = dati['catalog_address']
    location_service = dati['location_address']
    database_address = dati['database_address'] 
    service =  data_analysis_service(broker, port, service_ID, topic, catalog_address, location_service, database_address)

    done = False
    while not done:
        #mettere condizione di stop?
        time.sleep(1)