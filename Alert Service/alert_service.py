import json
import time
import requests

from MQTT import *
from TeleBot.MyMQTT import *   ### COSA SIGNIFICA????????? 
import requests as r
    
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


        # prende le informazioni necessarie 
        patient_ID = msg['patient_ID']
        measures = msg['e'][2:-1] # le prime 2 sono la posizione

        # itera lungo le misurazioni dei singoli sensori e controlla la criticità associata ad essa, nel caso ci sia un problema richiama i metodi di notifica 
        # i metodi per le procedure di allerta sono definiti sotto 
        for measure in measures:

            is_critical = json.loads(requests.get(self.catalog_address + '/get_critical_info', params= {'patient_ID':patient_ID, 's_ID':measure['n']}).text)
            
                                # messaggio ricevuto 
                                # is_critical = {
                                #  "type_ID": "s_1",
                                # 'safe_range':[numero1, numero2]
                                # 'is_critical':
                                # }

            if is_critical["is_critial"] == "not_critical":
                pass

            else: 
                if measure['v'] > is_critical['safe_range'][1] | measure['v'] < is_critical['safe_range'][0]:

                    # se la misurazione è informativa (allerta solo al paziente)
                    if is_critical["is_critial"] == "personal":
                        
                        #messaggio che viene mandato insieme alla notifica
                        problem = f'reading {measure["n"]}: {measure["v"]} {measure["u"]} out of safe range'
                        self.personal_alert(patient_ID,problem)

                    # se la misuzione è critica (allerta a clinica e medico)
                    if is_critical["is_critial"] == "critical":

                        #messaggio che viene mandato insieme alla notifica
                        problem = f'reading {measure["n"]}: {measure["v"]} {measure["u"]} out of safe range'
                        self.critical_alert(patient_ID,problem) # a questo punto chiamo la funzione alert (basta richiamarlo ogni volta)
                    

    # allerta critica (medico e clinica)
    def critical_alert(self,patient_ID,problem):

        # get al catalog per informazioni di contatto del medico 
        doctor = json.loads(r.get(self.catalog_address + 'get_doctor',data = {"patient_ID":patient_ID}).text)

        # template del messaggio ricevuto 
                                # msg = {
                                #   'name':''
                                #   'chat_ID':''
                                # }

        # get al location service per informazioni di contatto della clinica
        nearest_clinic = json.loads(r.get(self.location_service, data = {"patient_ID":patient_ID}).text)

        # template messaggio ricevuto:
                                # msg = {
                                #     'patient_ID':patient['patient_ID'],
                                #     'clinic_pos':'',
                                #     'patient_pos':'',
                                #     'nearest':'',
                                #     'clinic_chat_ID':"" 
                                #     })

        # nel caso in cui il campo nearest sia vuoto non entra in questo blocco e non manda il messaggio (non si conosce la posizione della clinica)
        if nearest_clinic['nearest']:    
           
            # messaggio da mandare alla clinica e al medico
            msg = {
                "patient_ID":patient_ID,
                "patient_location":
                    {
                    "latitude":nearest_clinic['patient_pos']['latitude'],
                    "longitude":nearest_clinic['patient_pos']["longitude"]
                    },
                "message":problem, # messaggio che verrà letto 
                "doctor_contact":doctor["chat_ID"],
                "doctor_name":doctor["name"], 
                "chat_ID":doctor["chat_ID"]
            }

            # contact info della clinica
            nearest_clinic_chat_ID = nearest_clinic['clinic_chat_ID']

            # messaggio mandato alla clinica
            self.alert_service.myPublish('clinic_alert/'+nearest_clinic_chat_ID, msg)

            # messaggio mandato al medico
            self.alert_service.myPublish("telebot/critical_alert", msg)
            print ('message correctly sent')
        else: 
            msg = {
                "patient_problem":problem, 
                "patient_ID":patient_ID,
                "location":"not known",
                "message":problem, # messaggio che verrà letto 
                "chat_ID":doctor["chat_ID"]
            }

            # messaggio mandato al medico 
            self.alert_service.myPublish("telebot/critical_alert", msg)

            print ('error: patient location unknown') # in questo caso manda solo un messaggio la medico (non è aggiornata la posizione del paziente)

    # allerta informativa (paziente)
    def personal_alert(self,patient_ID,problem):

        # get al catalog per informazioni di contatto del paziente
        patient = json.loads(r.get(self.catalog_address + 'get_patient',data = {"patient_ID":patient_ID}).text)

        # messaggio
        msg = {
            "message":problem,   
            "chat_ID":patient["chat_ID"]
        }

        # messaggio mandato al paziente (da aggiornare)
        self.alert_service.myPublish("telebot/personal_alert", msg)


if __name__ =='__main__':

####       CODICE DI "DEBUG"                                                            # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("./catalog.json",'r') as f:                                               # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]

####

    # with open("./config.json",'r') as f:
    #   catalog_address = json.load(f)["catalog_address"]

    # Ottiene dal catalog l'indirizzo del servizio di location
    location_service = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'location_service'}).text) # da modificare sul catalog
    settings = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'alert_service'}).text)
    mqtt_settings = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'MQTT'}).text)
    
    # carica i dati relativi al client MQTT e agli indirizzi del location service e del catalog manager
    topic = f"{mqtt_settings['baseTopic']}/{settings['topic']}"
    broker = mqtt_settings['broker']
    port = mqtt_settings['port']
    service_ID = settings['service_ID']
    location_address = f"{location_service['host']}:{location_service['port']}"

    # avvia il servizio (subscriber MQTT)
    service =  alert_service(broker, port, service_ID, topic, location_address, catalog_address)

    # mantiene il servizio attivo
    done = False
    while not done:
        time.sleep(1)

