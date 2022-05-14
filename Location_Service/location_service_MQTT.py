
from math import dist
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
        self.location_service = location_service

    # deve ricevere: template messaggio inviato: (va mddificato di conseguenza)
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
                                #       },
                                #       {               
                                #         'n':sensor_type,
                                #         'v':'',
                                #         'u':unit,
                                #         },

    # restituisce la location di un paziente, richiamata da alert service
    def GET(self, *uri, **params): 
            
        #estrae il dizionario relativo al paziente e lo restituisce alla clinica che dovrà fare un controllo sulla presenza o meno deella posizione calcolata
        msg = next((p for p in self.nearest if p['patient_ID'] == params["patient_ID"]), None) 

        return msg

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

        measures = msg['e']

        if measures[0]['n'] == 'lat' & measures[1]['n'] == 'lon':

        # alla prima iterazione (cioè quando i dizionari di self.clinics e di patient list sono vuoti) li inizializza, questo non è nell'init perchè il catalog e il location 
        # vengono inizializzati insieme, quindi all'inizio il catalog non può rispondere alle richieste
            if not self.clinics:

                #manda due richieste al catalog per la lista delle cliniche e dei pazienti (come scritte nel catalog)
                self.clinics = json.loads(r.get(self.catalog_address + '/get_clinics').text)
                self.patient_list = json.loads(r.get(self.catalog_address + '/get_patients').text)

                self.nearest = []

                # inizilizza una lista che contiene questi campi per ogni paziente, all'inizio la lista è vuota, verrà riempita man mano che le posizioni vengono ricevute
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
                "latitude":measures[0]["lat"],
                "longitude":measures[1]["lat"]
                }

            patient_ID = msg['patient_ID']

            # itera tra tutte le cliniche calcolando la distanza dal paziente per trovare quella più vicina
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
                
                clinic_location = clinic['clinic_location']

                #calcolo della piu vicina con la distanza euclidea
                d = dist([patient_location['longitude'],patient_location['latitude']],[clinic_location["longitude"],clinic_location["latitude"]])

                # se dist_temp è vuota (prima iterazione) la inizializza a d
                if not dist_temp: dist_temp = d

                # confronta sempre la distanza trovata con dist_temp e nel caso d sia inferiore
                # (la nuova clinica più vicina è stata trovata) aggiorna dist_temp e salva l'indice della clinica
                if d < dist_temp:
                    dist_temp = d
                    nearest_index = i 

            # cerca nella lista nearest inizializzata in precedenza il paziente di cui va aggiornata la posizione e salva l'indice
            for i, patient in enumerate(self.nearest):
                if patient['patient_ID'] == patient_ID:
                    p_index = i
                
            #aggiorna la posizione
            self.nearest[p_index]['nearest'] == self.clinics[nearest_index]['clinic_id']
            self.nearest[p_index]['patient_pos'] == msg['pos']
            self.nearest[p_index]['clinic_pos'] == self.clinics[nearest_index]['clinic_location']
            self.nearest[p_index]['clinic_address'] = 'alert/clinica1'


#####################################################################################################


if __name__ == '__main__':

    ####       CODICE DI "DEBUG"                                                        # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("Catalog/catalog.json",'r') as f:                                                 # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]
    ####
    
    settings = json.loads(r.get(f"{catalog_address}/get_service_info", params={'service_ID': 'location_service'}).text)
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
    # this is needed if you want to have the custom error page
    # cherrypy.config.update({'error_page.400': error_page_400}) # potremmo metterla anche noi questa pagina
    cherrypy.engine.start()
    cherrypy.engine.block()

