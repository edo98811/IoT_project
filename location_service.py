
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


    def GET(self, *uri, **params): #da riguardare come funzionano bene i rest
        p_ID = params["p_ID"]#['patient_id']
            
        patient_info = next((p for p in self.nearest if p['d_ID'] == p_ID), None) #estrae il dizionario relativo al paziente e lo restituisce alla clinica che dovrà fare un controllo sulla presenza o meno dei campi 

        return patient_info
        
    @cherrypy.tools.json_in()
    def POST(self, *uri, **payload): #è giusto in questo modo?
        msg=cherrypy.request.json
        if not self.clinics:
            #posso mandare richieste al server stesso secondo google quindi dovrebbe essere ok
            self.clinics = json.loads(requests.get(self.catalog_address + '/get_clinics').text) #mettere in modo che i formati che escano dalle richieste siano corretti 
            self.patient_list = json.loads(requests.get(self.catalog_address + '/get_patients').text)

            self.nearest = []

            for patient in self.patient_list: 

                self.nearest.append({
                    'patient_ID':patient['patient_ID'],
                    'clinic_pos':'',
                    'patient_pos':'',
                    'nearest':'',
                    'clinic_address':'', #mandato questo json (che viene mandato così perchè viene estratto da questa lista)
                })

        #msg = json.loads(payload)

        pat_pos = msg['location']
        p_ID = msg['p_ID']

        for clinic,i in enumerate(self.clinics):

            cl_pos = clinic['clinic_pos']

            #calcolo della piu vicina
            d = dist([pat_pos['longitude'],pat_pos['latitude']],[cl_pos["longitude"],cl_pos["latitude"]])
            if d < dist_temp:
                dist_temp = d
                nearest_index = i #prende l'indice della clinica più viina la paziente

        for patient, i in enumerate(self.nearest): #cerca l'indice del paziene nel json con le posizione per poterla aggiornare
            if patient['patient_ID'] == p_ID:
                p_index = i
            

        #aggiorna la posizione 
        self.nearest[p_index]['nearest'] == self.clinics_pos[nearest_index]['clinic_id']
        self.nearest[p_index]['patient_pos'] == msg['pos']
        self.nearest[p_index]['clinic_pos'] == self.clinics_pos[nearest_index]['clinic_pos']

    #def update_pos(self): forse non serve


