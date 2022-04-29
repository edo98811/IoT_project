import json
#import requests
import cherrypy

class catalog():
    exposed=True
    def __init__(self,catalog_file):
        self.catalog_file = catalog_file

    def GET(self,*uri,**params): 
        # legge il catalog dal file json e lo carica in una variabile temporanea catalog 
        catalog = json.load(open(self.catalog_file,'r'))

        # device connector info
        if uri[0] == 'get_dc_info':

            # richiamato da device connector      

              
            p_ID = params['p_ID']

            # questa funzione crea un iterator della lista e mi restituisce le informazioni 
            # sul paziente identificato dal p_ID passato alla funzione
            # spiegato male: un iterator è un oggetto che applica una funzione ad un altro oggetto 
            pat = next((p for p in catalog['patients'] if p['patient_ID'] == p_ID ), None) 

            msg = {
                "broker":pat["device_connector"]["topic"],
                "port":pat["device_connector"]["port"],
                "topic":catalog["MQTT_broker"],
            }

            return json.dumps(msg)

        #sensori relativi ad un paziente
        elif uri[0] == 'get_sensors':

            # richiamato da device connector

            p_ID = params['p_ID']
          
            # prende le info del paziente a recupera la lista dei sensori
            pat = next((p for p in catalog['patients'] if p['patient_ID'] == p_ID ), None)
            sensor_ids = pat["sensors"]
            sensors = []

            # itera lungo la lista dei sensori e prende le loro informazioni dal catalog
            for s_info in sensor_ids:

                
                # recupera le carattersitiche dei sensori
                s_type = next((s for s in catalog['sensors'] if s['type_ID'] == s_info['type'] ), None)

                # questo è il messaggio passato al sensor info del device connector
                s_msg = {
                    "is_critical":s_info["is_critical"],
                    "safe_range":s_info["safe_range"],
                    "type_ID":s_type["type_ID"],
                    "type":s_type["type"],
                    "range":s_type["range"],
                    "unit":s_type["unit"]
                }

                # lo aggiunge ad una lista
                sensors.append(s_msg)

            # dato che la lista non si può mandare in un json creo un messaggio con una chiave associata alla lista

            msg ={
                'sl':sensors
            } 
            return json.dumps(sensors)


        #per le cliniche
        elif uri[0] == 'get_clinics':
            # richiamata da alert_service
        
            clinics = catalog["clinics"]

            return json.dumps(clinics)

        #per le informazioni di un paziente

            # richiamato da: alert_service

        elif uri[0] == 'get_patient_info':
            p_ID = params["p_ID"]

            # richiamato da alert service

            patient = next((p for p in catalog['patients'] if p['patient_ID'] == p_ID), None)  
            return json.dumps(patient)

        # #per tutti i pazienti 
        # elif uri[0] == 'get_patients':
        #     # richiamato da

        #     return json.dumps(catalog['patients'])

        #per il dottore associato ad un paziente
        elif uri[0] == 'get_doctor':
            
            # prima trova il paziente per cui devo ricercare il medico
            p_ID = params["p_ID"] 
            patient = next((p for p in catalog['patients'] if p['patient_ID'] == p_ID), None) 

            # poi cerco le informazioni del medico salvate nella lista dei medici
            d_ID = patient["doctor_ID"]
            doctor = next((d for d in catalog['doctors'] if d['doctor_ID'] == d_ID), None) 

            return json.dumps(doctor) 
        
        else: 
            raise cherrypy.HTTPError(
                400,
                "The request entity could not be decoded. The following command doesn't exist {uri[0]}")
            pass

    def POST():
        pass
        #addsensor
        #addpatient
        #adddoctor
        #addclinic

    