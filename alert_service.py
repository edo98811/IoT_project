import json
import time
import requests

from MQTT import *
from MyMQTT import *
import requests as r
#ahdgkldgjag
#emanuele

    
class alert_service:
    def __init__(self, broker, port, ID, topic,catalog_address,location_service):
        self.alert_service = MyMQTT(ID, broker, int(port), self)
        self.alert_service.start()
        self.alert_service.mySubscribe(topic)
        self.catalog_address = catalog_address 
        self.location_service = location_service

    def notify(self, topic, msg): 


        # messaggio ricevuto da device connector
        # template messaggio: 

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
                #         },
                #         {               
                #         'n':sensor_ID,
                #         'vs':sensor_type,
                #         'v':'',
                #         't':time,
                #         'u':unit,
                #         },
                #     ]
                #     'latitude':0,
                #     'longitude':0
                # }

        # prende le informazioni necessarie 
        patient_ID = msg['p_ID']
        measures = msg['e']

        # itera lungo le misurazioni dei singoli sensori e controlla la criticità associata ad essa, nel caso ci sia un problema richiama i metodi di notifica 
        # i metodi per le procedure di allerta sono definiti sotto 
        for measure in measures:

            is_critical =json.loads(requests.get(self.catalog_address + '/get_critical_info', params= {'p_ID':patient_ID, 's_ID':measure['n']}).text)
            # messaggio ricevuto 
            # is_critical = {
            # 'safe_range':''
            # 'is_critical':[numero1, numero2]
            # }
   
            if measure["is_critial"] == "not_critical":
                pass

            # se la misurazione è informativa (allerta solo al paziente)
            if measure["is_critial"] == "informative":


                #messaggio che viene mandato insieme alla notifica
                problem = f'lettura di {measure["vs"]} di {measure["v"]} fuori dal range di sicurezza impostato da {measure["v"][0]} a {measure["v"][1]}'
                self.informative_alert(patient_ID,problem)

            # se la misuzione è critica (allerta a clinica e medico)
            if measure["is_critial"] == "critical":

                #messaggio che viene mandato insieme alla notifica
                problem = f'lettura di {measure["vs"]} di {measure["v"]} fuori dal range di sicurezza impostato da {measure["v"][0]} a {measure["v"][1]}'
                self.critical_alert(patient_ID,problem) # a questo punto chiamo la funzione alert (basta richiamarlo ogni volta)
            

    # allerta critica (medico e clinica)
    def critical_alert(self,patient_ID,problem):


        # get al catalog per informazioni di contatto del medico 
        doctor = json.loads(r.get(self.catalog_address + 'get_doctor',data = {"p_ID":patient_ID}).text)

        #print("attenzioneeee" + patient_ID + " sta morendo")
        # messaggio da mandare alla clinica e al medico
        msg = {
                "p_ID":patient_ID,
                "latitude":nearest_clinic['patient_pos']['longitudine'],
                "longitude":nearest_clinic['patient_pos']['latitudine'],
                "problem":problem, # messaggio che verrà letto
                "doctor_contact":doctor["chat_ID"]
            }

        # ricava il contatto (ha ricevuto tutte le info)
        contact = doctor["chat_ID"]

        # messaggio mandato al dottore
        self.alert_service.myPublish('telepot/alert/message', msg)

        # get al location service per informazioni di contatto della clinica
        nearest_clinic = json.loads(r.get(self.location_service, data = {"p_ID":patient_ID}).text)
            # template messaggio ricevuto:
                    # msg = {
                    #     'patient_ID':patient['patient_ID'],
                    #     'clinic_pos':'',
                    #     'patient_pos':'',
                    #     'nearest':'',
                    #     'clinic_address':"" 
                    #     })

        topic = nearest_clinic["clinic_address"]

        # nel caso in cui il campo nearest sia vuoto non entra in questo blocco e non manda il messaggio (non si conosce la posizione della clinica)
        if nearest_clinic['nearest']:    
          
            # messaggio da mandare alla clinica e al medico
            msg = {
                "p_ID":patient_ID,
                "latitude":nearest_clinic['patient_pos']['longitudine'],
                "longitude":nearest_clinic['patient_pos']['latitudine'],
                "problem":problem, # messaggio che verrà letto 
                "doctor_contact":doctor["chat_ID"],
                "doctor_name":doctor["name"] # magari da correggere
            }

            # messaggio mandato alla clinica
            self.alert_service.myPublish(topic, msg)
            print ('messaggio mandato correttamente alla clinica')
        else: 
            print ('errore, non si conosce la posizione del paziente') # in questo caso manda solo un messaggio la medico (non è aggiornata la posizione del paziente)

    # allerta informativa (paziente)
    def informative_alert(self,patient_ID,problem):
        # get al catalog per informazioni di contatto del paziente
        patient = json.loads(r.get(self.catalog_address + 'get_patient',data = {"p_ID":patient_ID}).text)

        contact = patient["chat_ID"]
        # messaggio
        msg = {
            "message":problem
        }

        # messaggio mandato al paziente (da aggiornare)
        self.alert_service.myPublish('telepot/alert/message', msg)




if __name__ =='__main__':

####       CODICE DI "DEBUG"                                                            # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("./catalog.json",'r') as f:                                               # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]
####
  
    # Ottiene dal catalog l'indirizzo del servizio di location
    s = requests.session()
    location = s.get(catalog+"/service-address?name=location_service")

    # carica i dati relativi al client MQTT e agli indirizzi del location service e del catalog manager
    dati = json.load(open('settings_as.json','r')) 
    topic = dati['topic']
    broker = dati['broker']
    port = dati['port']
    service_ID = dati['service_ID']
    # avvia il servizio (subscriber MQTT)
    service =  alert_service(broker, port, service_ID, topic,location, catalog)

    done = False
    while not done:
        time.sleep(1)
