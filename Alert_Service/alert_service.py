import json
import time
import requests

from MyMQTT import *
import requests as r
    
class alert_service:
    def __init__(self, broker, port, ID, topic,location_service,catalog_address):
        self.alert_service = MyMQTT(ID, broker, int(port), self)
        self.alert_service.start()
        self.alert_service.mySubscribe(topic)
        self.catalog_address = catalog_address 
        self.location_service = location_service
        self.baseTopic = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'MQTT'}).text)["baseTopic"]

    def notify(self, topic, msg): 

        # messaggio ricevuto da device connector
        # template messaggio: 
                                # message = {			
                                # 'bn':patient_ID,
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
        # print(msg) 
        msg = json.loads(msg)
        patient_ID = msg['bn']
        measures = msg['e'][2:] # le prime 2 sono la posizione

        # itera lungo le misurazioni dei singoli sensori e controlla la criticità associata ad essa, nel caso ci sia un problema richiama i metodi di notifica 
        # i metodi per le procedure di allerta sono definiti sotto 
        # print(measures)
        sensor_info_list = json.loads(requests.get(self.catalog_address + '/get_critical_info', params= {'patient_ID':patient_ID}).text)["sensors"]
        sensor_info = json.loads(r.get(self.catalog_address + '/get_sensors',params = {"patient_ID":patient_ID}).text)

    
        for n,measure in enumerate(measures):


            is_critical = next((s for s in sensor_info_list if s['type_ID'] == measure['n'] ), None)
            # print(f'{measure["n"]} - {patient_ID} - {is_critical["is_critical"]}')
        
                                # Dmessaggio ricevuto 
                                #       is_critical = {
                                #        "type_ID": "s_1",
                                #       'safe_range':[numero1, numero2]
                                #       'is_critical':
                                # }

            if is_critical["is_critical"] == "not_critical":
                pass

            else: 
                if float(measure['v']) > float(is_critical['safe_range'][1]) or float(measure['v']) < float(is_critical['safe_range'][0]):
                    
                    patient_info = json.loads(r.get(self.catalog_address + '/get_patient_info',params = {"patient_ID":patient_ID}).text)
                    problem = f"{patient_info['personal_info']['name']} {patient_info['personal_info']['surname']} - reading {sensor_info[n]['type']}: {measure['v']} {measure['u']}, out of safe range!!!"

                    # se la misurazione è informativa (allerta solo al paziente)
                    if is_critical["is_critical"] == "personal":
                        
                        #messaggio che viene mandato insieme alla notifica
                        self.personal_alert(patient_ID,problem)

                    # se la misuzione è critica (allerta a clinica e medico)
                    if is_critical["is_critical"] == "critical":

                        #messaggio che viene mandato insieme alla notifica
                        
                        #problem = f'reading {measure["n"]}: {measure["v"]} {measure["u"]} out of safe range'
                        self.critical_alert(patient_ID,problem) # a questo punto chiamo la funzione alert (basta richiamarlo ogni volta)
                
    # allerta critica (medico e clinica)
    def critical_alert(self,patient_ID,problem):

        print(f'critical alert{patient_ID} - {problem}')
        # get al catalog per informazioni di contatto del medico 
        doctor = json.loads(r.get(self.catalog_address + '/get_doctor_info',params = {"patient_ID":patient_ID}).text)

        # template del messaggio ricevuto 
                                # msg = {
                                #   'name':''
                                #   'chat_ID':''
                                # }

        # get al location service per informazioni di contatto della 
        # print(self.location_service)
        nearest_clinic = json.loads(r.get(self.location_service, params = {"patient_ID":patient_ID}).text)

        patient_info = json.loads(r.get(self.catalog_address + '/get_patient_info',params = {"patient_ID":patient_ID}).text)
        
        # template messaggio ricevuto:
                                # msg = {
                                #     'patient_ID':patient['patient_ID'],
                                #     'clinic_pos':'',
                                #     'patient_location':'',
                                #     'nearest':'',
                                #     'clinic_topic':"" 
                                #     })

        # nel caso in cui il campo nearest sia vuoto non entra in questo blocco e non manda il messaggio (non si conosce la posizione della clinica)
        if nearest_clinic['nearest']:    
            patient_info = json.loads(r.get(self.catalog_address + '/get_patient_info',params = {"patient_ID":patient_ID}).text)
   
            # messaggio da mandare alla clinica e al medico
            msg = {
                "patient_ID":patient_ID,
                "full_name": f"{patient_info['personal_info']['name']} {patient_info['personal_info']['surname']}",
                "patient_location":
                    {
                    "latitude":nearest_clinic['patient_location']['latitude'],
                    "longitude":nearest_clinic['patient_location']["longitude"]
                    },
                "message":problem, # messaggio che verrà letto 
                "doctor_name":doctor["name"], 
                "chat_ID":doctor["chat_ID"]
            }

            # contact info della clinica
            nearest_clinic_topic = nearest_clinic['clinic_topic']
            basetopic = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'MQTT'}).text)["baseTopic"]

            # messaggio mandato alla clinica
            self.alert_service.myPublish(basetopic + '/'+ nearest_clinic_topic, msg)

            # messaggio mandato al medico
            telebot_critical = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'telegram_bot'}).text)["critical_alert_topic"]
            self.alert_service.myPublish(basetopic + '/' + telebot_critical , msg)
            print (f'message correctly sent - topic:{telebot_critical}')
        
        else: 
            msg = { 
                "patient_ID":patient_ID,
                "full_name": f"{patient_info['personal_info']['name']} {patient_info['personal_info']['surname']}",
                "location":"not known",
                "message":problem, # messaggio che verrà letto 
                "chat_ID":doctor["chat_ID"]
            }

            # messaggio mandato al medico 
            telebot_critical = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'telegram_bot'}).text)["critical_alert_topic"]
            self.alert_service.myPublish(self.baseTopic+ '/' + telebot_critical , msg)

            print ('error: patient location unknown') # in questo caso manda solo un messaggio la medico (non è aggiornata la posizione del paziente)

    # allerta informativa (paziente)
    def personal_alert(self,patient_ID,problem):

        # get al catalog per informazioni di contatto del paziente
        print(f'personal alert - {patient_ID} - {problem}')
        patient = json.loads(r.get(self.catalog_address + '/get_patient_info',params = {"patient_ID":patient_ID}).text)

        # messaggio
        msg = {
            "message":problem,   
            "chat_ID":patient["personal_info"]["chat_ID"]
        }

        # messaggio mandato al paziente (da aggiornare)
        telebot_personal = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'telegram_bot'}).text)["personal_alert_topic"]
        
        self.alert_service.myPublish(self.baseTopic + '/' + telebot_personal , msg)


if __name__ =='__main__':

####       CODICE DI "DEBUG"                                                            # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("config.json",'r') as f:                                               # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                           # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["address"]

    print(catalog_address)
####
  
    # Ottiene dal catalog l'indirizzo del servizio di location
    # s = requests.session() # session non dovrebbe servire a noi: https://realpython.com/python-requests/#the-session-object

    settings = json.loads(r.get(f"{catalog_address}/get_service_info", params={'service_ID': 'alert_service'}).text)
    mqtt_settings = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'MQTT'}).text)
    
    topic = f"{mqtt_settings['baseTopic']}/{settings['topic']}"
    broker = mqtt_settings['broker']
    port = mqtt_settings['port']
    service_ID = settings['service_ID']

    location_service_settings = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'location_service'}).text) # da modificare sul catalog

    location_address = f'http://{location_service_settings["host"]}:{location_service_settings["port"]}'
    # print(location_address)
    # avvia il servizio (subscriber MQTT)
    service =  alert_service(broker, port, service_ID, topic, location_address, catalog_address)

    # mantiene il servizio attivo
    done = False
    while not done:
        time.sleep(2)

