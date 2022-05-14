
from math import dist
import json
import time
import requests
import cherrypy



class location_service():
    exposed=True
    def __init__(self,catalog_address):
        self.catalog_address = catalog_address
        self.clinics = []
        self.patient_list = []

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
        patient_ID = params["patient_ID"]
            
        #estrae il dizionario relativo al paziente e lo restituisce alla clinica che dovrà fare un controllo sulla presenza o meno deella posizione calcolata
        msg = next((p for p in self.nearest if p['patient_ID'] == patient_ID), None) 

        return msg

    #@cherrypy.tools.json_in()
    def POST(self, *uri, **params):

        #payload del messaggio di POST 
        msg=cherrypy.request.json

        # alla prima iterazione (cioè quando i dizionari di self.clinics e di patient list sono vuoti) li inizializza, questo non è nell'init perchè il catalog e il location 
        # vengono inizializzati insieme, quindi all'inizio il catalog non può rispondere alle richieste
        if not self.clinics:

            #manda due richieste al catalog per la lista delle cliniche e dei pazienti (come scritte nel catalog)
            self.clinics = json.loads(requests.get(self.catalog_address + '/get_clinics').text)
            self.patient_list = json.loads(requests.get(self.catalog_address + '/get_patients').text)

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

        # estrae dal dizionario ricevuto la posizione e l'ID del paziente
        # il messaggio ora come ora è così strutturato (bisogna vedere cosa se ne farà del data analysis): 
        # template messaggio ricevuto: 
                                # msg = {			
                                # 'patient_ID':patient_ID,
                                # 't':basetime,
                                # 'e':[ 
                                #       {               
                                #         'n':sensor_ID,
                                #         'vs':sensor_type,
                                #         'v':'value',
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
                                #   ]
                                #   'location':{        #un problema concettuale è che avendo la posizione qui non serve forse chiamare il catalog service
                                #       'latitude':0,
                                #       'longitude':0
                                #   } 
                                # }

        patient_location = msg['location']
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

        for clinic,i in enumerate(self.clinics): 
            
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
        for patient, i in enumerate(self.nearest):
            if patient['patient_ID'] == patient_ID:
                p_index = i
            
        #aggiorna la posizione
        self.nearest[p_index]['nearest'] == self.clinics[nearest_index]['clinic_id']
        self.nearest[p_index]['patient_pos'] == msg['pos']
        self.nearest[p_index]['clinic_pos'] == self.clinics[nearest_index]['clinic_location']
        self.nearest[p_index]['clinic_address'] = 'alert/clinica1'



