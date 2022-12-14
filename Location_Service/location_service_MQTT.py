
import math
import json
import time
import requests as r
import cherrypy

from MyMQTT import *


class location_service():
    exposed=True
    def __init__(self,broker, port, service_ID, topic, catalog_address):
        self.catalog_address = catalog_address
        self.clinics = []
        self.patient_list = []
        self.loc_service = MyMQTT(service_ID, broker, int(port), self)
        self.loc_service.start()
        self.loc_service.mySubscribe(topic)
        self.catalog_address = catalog_address # tutti gli indirizzi si potrebbero salvare nel catalog e prenderli all'inizio con una richiwsta e poi aggiungere un controllo negli errori nel caso 

        print(topic)
    # deve ricevere: template messaggio inviato: (va mddificato di conseguenza)
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
                                #       },
                                #       {               
                                #         'n':sensor_type,
                                #         'v':'',
                                #         'u':unit,
                                #         },

    # restituisce la location di un paziente, richiamata da alert service
    def GET(self, *uri, **params): 
            
        #estrae il dizionario relativo al paziente e lo restituisce alla clinica corretta
        return json.dumps(next((p for p in self.nearest if p['patient_ID'] == params["patient_ID"]), None))

    def notify(self, topic, msg):
        #print('funzionaa')

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

        measures = msg['e']

        if measures[0]['v'] and measures[1]['v']:

        # alla prima iterazione (cio?? quando i dizionari di self.clinics e di patient list sono vuoti) li inizializza, questo non ?? nell'init perch?? il catalog e il location 
        # vengono inizializzati insieme, quindi all'inizio il catalog non pu?? rispondere alle richieste
            if not self.clinics:
                
                #manda due richieste al catalog per la lista delle cliniche e dei pazienti (come scritte nel catalog)
                self.clinics = json.loads(r.get(self.catalog_address + '/get_clinics').text)
                self.patient_list = json.loads(r.get(self.catalog_address + '/get_patients').text)

                self.nearest = []

                # inizilizza una lista che contiene questi campi per ogni paziente, all'inizio la lista ?? vuota, verr?? riempita man mano che le posizioni vengono ricevute
                # struttura: [{info posizione paziente 1},{info posizione paziente 2}...]
                for patient in self.patient_list: 

                    self.nearest.append({
                        'patient_ID':patient['patient_ID'],
                        'clinic_location':'',
                        'patient_location':'',
                        'nearest':'',
                        'clinic_address':"" 
                    })

            patient_location = {
                "latitude":measures[0]["v"],
                "longitude":measures[1]["v"]
                }

            patient_ID = msg['bn']

            # itera tra tutte le cliniche calcolando la distanza dal paziente per trovare quella pi?? vicina
            # la lista delle cliniche ha questa struttura (come nel catalog):
                        #   [{
                        #     "clinic_ID": "cl_1",
                        #     "location": {
                        #       "longitude": "40000",
                        #       "latitude": "013000"
                        #     }
                        #   },
                        #   ... ]

            for i,clinic in enumerate(self.clinics): 
                
                clinic_location = clinic['location']

                #calcolo della piu vicina con la distanza euclidea
                d = math.dist([float(patient_location['longitude']),float(patient_location['latitude'])],[float(clinic_location["longitude"]),float(clinic_location["latitude"])])

                # se dist_temp ?? vuota (prima iterazione) la inizializza a d
                try:
                    dist_temp
                except NameError:
                    dist_temp = d

                nearest_index = 0

                # confronta sempre la distanza trovata con dist_temp e nel caso d sia inferiore
                # (la nuova clinica pi?? vicina ?? stata trovata) aggiorna dist_temp e salva l'indice della clinica
                if d < dist_temp:
                    dist_temp = d
                    nearest_index = i 

            # cerca nella lista nearest inizializzata in precedenza il paziente di cui va aggiornata la posizione e salva l'indice
            for i, patient in enumerate(self.nearest):
                if patient['patient_ID'] == patient_ID:
                    p_index = i
                
            #aggiorna la posizione
            self.nearest[p_index]['nearest'] = self.clinics[nearest_index]['clinic_ID']
            self.nearest[p_index]['patient_location'] = patient_location
            self.nearest[p_index]['clinic_location'] = self.clinics[nearest_index]['location']
            self.nearest[p_index]['clinic_topic'] = self.clinics[nearest_index]['clinic_topic'] # aggiungere il basetopic

            #print (json.dumps(self.nearest))
            time.sleep(0.1)


#####################################################################################################


if __name__ == '__main__':

    ####                                                           
    with open("config.json",'r') as f:                                                
        cat = json.load(f)                                                           
    host = cat["base_host"]                                                      
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+ cat["address"]
    ####
    
    settings = json.loads(r.get(catalog_address + "/get_service_info", params={'service_ID': 'location_service'}).text)
    mqtt_settings = json.loads(r.get(catalog_address +"/get_service_info", params = {'service_ID':'MQTT'}).text)
    
    topic = f"{mqtt_settings['baseTopic']}/{settings['topic']}"
    broker = mqtt_settings['broker']
    port = mqtt_settings['port']
    service_ID = settings['service_ID']

    conf = {
        '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tool.session.on': True
        }
    }

    cherrypy.tree.mount(location_service(broker, port, service_ID, topic, catalog_address), '/', conf)
      
    cherrypy.config.update({'server.socket_host': settings['host'],
                            'server.socket_port': int(settings['port'])})
    
    # cherrypy.config.update({'error_page.400': error_page_400}) # potremmo metterla anche noi questa pagina
    cherrypy.engine.start()
    cherrypy.engine.block()

