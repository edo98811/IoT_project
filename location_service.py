
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

    # restituisce la location di un paziente, richiamata da alert service
    def GET(self, *uri, **params): 
        p_ID = params["p_ID"]
            
        #estrae il dizionario relativo al paziente e lo restituisce alla clinica che dovrà fare un controllo sulla presenza o meno deella posizione calcolata
        patient_info = next((p for p in self.nearest if p['patient_ID'] == p_ID), None) 

        return patient_info

    @cherrypy.tools.json_in()
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
                    'clinic_pos':'',
                    'patient_pos':'',
                    'nearest':'',
                    'clinic_address':"" 
                })

        # estrae dal dizionario ricevuto la posizione e l'ID del paziente
        # il messaggio ora come ora è così strutturato (bisogna vedere cosa se ne farà del data analysis): 
                    # msg = {
                    #     "p_ID":patient_ID,
                    #     "s_ID":measure['n'],
                    #     "location": {
                    #         "latitude":
                    #         "longitude":
                    #     }
                    # }

        pat_pos = msg['location']
        p_ID = msg['p_ID']


        # itera tra tutte le cliniche calcolando la distanza dal paziente per trovare quella più vicina
        # la lista delle cliniche ha questa struttura (come nel catalog):
                    #   [{
                    #     "clinic_ID": "cl_1",
                    #     "position": {
                    #       "longitude": "40000",
                    #       "latitude": "013000"
                    #     }
                    #   },
                    #   ... ]

        for clinic,i in enumerate(self.clinics): 
            
            cl_pos = clinic['clinic_pos']

            #calcolo della piu vicina con la distanza euclidea
            d = dist([pat_pos['longitude'],pat_pos['latitude']],[cl_pos["longitude"],cl_pos["latitude"]])

            # se dist_temp è vuota (prima iterazione) la inizializza a d
            if not dist_temp: dist_temp = d

            # confronta sempre la distanza trovata con dist_temp e nel caso d sia inferiore
            # (la nuova clinica più vicina è stata trovata) aggiorna dist_temp e salva l'indice della clinica
            if d < dist_temp:
                dist_temp = d
                nearest_index = i 

        # cerca nella lista nearest inizializzata in precedenza il paziente di cui va aggiornata la posizione e salva l'indice
        for patient, i in enumerate(self.nearest):
            if patient['patient_ID'] == p_ID:
                p_index = i
            
        #aggiorna la posizione
        self.nearest[p_index]['nearest'] == self.clinics_pos[nearest_index]['clinic_id']
        self.nearest[p_index]['patient_pos'] == msg['pos']
        self.nearest[p_index]['clinic_pos'] == self.clinics_pos[nearest_index]['clinic_pos']
        self.nearest[p_index]['clinic_address'] = 'alert/clinica1'



