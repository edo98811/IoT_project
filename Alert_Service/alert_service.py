import json
import time
import requests as r

from MyMQTT import *
    
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
        print(f"message received from: {patient_ID}")
        # itera lungo le misurazioni dei singoli sensori e controlla la criticità associata ad essa, nel caso ci sia un problema richiama i metodi di notifica 
        # i metodi per le procedure di allerta sono definiti sotto 
        # print(measures)
        sensor_info_list = json.loads(r.get(self.catalog_address + '/get_critical_info', params= {'patient_ID':patient_ID}).text)["sensors"]
        sensor_info = json.loads(r.get(self.catalog_address + '/get_sensors',params = {"patient_ID":patient_ID}).text)

    
        for n,measure in enumerate(measures):
            
            patient_info = json.loads(r.get(self.catalog_address + '/get_patient_info',params = {"patient_ID":patient_ID}).text)        
            is_critical = next((s for s in sensor_info_list if s['type_ID'] == measure['n'] ), None)
            # print(f'{measure["n"]} - {patient_ID} - {is_critical["is_critical"]}')
        
                                # Dmessaggio ricevuto 
                                #       is_critical = {
                                #        "type_ID": "s_1",
                                #       'safe_range':[numero1, numero2]
                                #       'is_critical':
                                # }
            print(f"    sensor {n}, type: {measure['n']}, critical info: {is_critical['is_critical']}")
            if is_critical["is_critical"] == "not_critical":
                pass

            elif is_critical["is_critical"] == "personal":
                
                part1 = f"Pay attention {patient_info['personal_info']['name']} {patient_info['personal_info']['surname']}!\n\
                Your device ({sensor_info[n]['type']}) is recording a value outside of your safe range"

                if float(measure['v']) > float(is_critical['safe_range'][1]): 
                    part2 = f"({measure['v']} {sensor_info[n]['unit']} > {is_critical['safe_range'][1]} {sensor_info[n]['unit']})\n\
                        Please, follow this measure (suggested by your personal doctor):\n\
                                {sensor_info[n]['over_safe']}"
                    self.personal_alert(patient_ID, f"{part1} {part2}")

                    print(f"        reading out of critical range: read{measure['v']} critical range {is_critical['safe_range'][0]}-{is_critical['safe_range'][1]}")

                elif float(measure['v']) < float(is_critical['safe_range'][0]): 
                    part2 = f"({measure['v']} {sensor_info[n]['unit']} < {is_critical['safe_range'][1]} {sensor_info[n]['unit']})\n\
                        Please, follow this measure (suggested by your personal doctor):\n\
                        {sensor_info[n]['under_safe']}"
                    self.personal_alert(patient_ID, f"{part1} {part2}")

                    print(f"        reading out of critical range: read{measure['v']} critical range {is_critical['safe_range'][0]}-{is_critical['safe_range'][1]}")

            elif is_critical["is_critical"] == "critical":
                if (float(measure['v']) > float(is_critical['safe_range'][1])) or (float(measure['v']) < float(is_critical['safe_range'][0])): #and time.time - self.time_s > self.tl:
                    problem = f"Warning! Critical event ongoing for patient: {patient_info['personal_info']['name']} {patient_info['personal_info']['surname']}\n\
                        Recorded by device: {sensor_info[n]['type']}\n\
                        Value: {measure['v']} {sensor_info[n]['unit']}\n\
                        Patient location:\n\
                            \tlat = {msg['e'][0]['v']}\n\
                            \tlon = {msg['e'][1]['v']}\n\
                        "
                    self.critical_alert(patient_ID,problem) # a questo punto chiamo la funzione alert (basta richiamarlo ogni volta)

                    print(f"        reading out of critical range: read{measure['v']} critical range {is_critical['safe_range'][0]}-{is_critical['safe_range'][1]}")
            else: 
                pass
        
                
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
            #print (f'message correctly sent - topic:{nearest_clinic_topic}')

            # messaggio mandato al medico
            telebot_critical = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'telegram_bot'}).text)["critical_alert_topic"]
            self.alert_service.myPublish(basetopic + '/' + telebot_critical , msg)
            #print (f'message correctly sent - topic:{telebot_critical}')
        
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

            #print ('error: patient location unknown') # in questo caso manda solo un messaggio la medico (non è aggiornata la posizione del paziente)

    # allerta informativa (paziente)
        print(f"         critical alert message sent to: {self.baseTopic + '/' + telebot_critical}")
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
        print(f"         personal alert message sent to: {self.baseTopic + '/' + telebot_personal}")

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
    # s = r.session() # session non dovrebbe servire a noi: https://realpython.com/python-r/#the-session-object

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

