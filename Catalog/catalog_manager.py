import json
import requests
import cherrypy
import os
# va aggiunto un controllo params in tutte le funzioni del codice

# nell'uri metto solo il tipo di richiesta (quindi da chi viene) 
# ma devo tenere conto che c'è anche la prima parte dell'indirizzo 

# importante far quadrare tutti i nomi di tutti 

class catalog():
    exposed=True

    def __init__(self,catalog_file):
        self.catalog_file = catalog_file

    def GET(self,*uri,**params): 

        # legge il catalog dal file json e lo carica in una variabile temporanea catalog 
        with open(self.catalog_file,'r') as f:
            catalog = json.load(f)

        if uri[0] == 'get_dc_info':                 # per informazioni necessarie per l'avvio del device connector

            # richiamato da device connector    

            # questa funzione crea un iterator della lista e mi restituisce le informazioni 
            # sul paziente identificato dal patient_ID passato alla funzione
            # spiegato male: un iterator è un oggetto che applica una funzione ad un altro oggetto 
            patient = next((p for p in catalog['patients'] if p['patient_ID'] == params['patient_ID'] ), None) 

            msg = {
                "broker":catalog["services"]["MQTT"]["broker"],
                "port":catalog["services"]["MQTT"]["port"],
                "topic":f'{catalog["services"]["MQTT"]["baseTopic"]}/{patient["device_connector"]["topic"]}'
            }

            return json.dumps(msg)

        elif uri[0] == 'get_sensors':               # per sensori relativi ad un paziente

            # richiamato da device connector
          
            # prende le info del paziente a recupera la lista dei sensori
            patient = next((p for p in catalog['patients'] if p['patient_ID'] == params['patient_ID'] ), None)
            sensors_info = patient["sensors"]
            sensors = []

            # itera lungo la lista dei sensori e prende le loro informazioni dal catalog
            for s_info in sensors_info:
                
                # recupera le carattersitiche dei sensori 
                s_type = next((s for s in catalog["sensors_type"] if s['type_ID'] == s_info['type_ID'] ), None)

                # questo è il messaggio passato al sensor info del device connector
                s_msg = {
                    "type_ID":s_type["type_ID"],
                    "type":s_type["type"],
                    "range":s_type["range"],
                    "safe_range":s_info["safe_range"],
                    "unit":s_type["unit"]
                }

                # lo aggiunge ad una lista
                sensors.append(s_msg)

            # dato che la lista non si può mandare in un json creo un messaggio con una chiave associata alla lista

            msg ={
                'sl':sensors
            } 
            return json.dumps(sensors)

        elif uri[0] == 'get_clinics':               # per info su tutte le cliniche

            # richiamata da location_service
            return json.dumps(catalog["clinics"])

        elif uri[0] == 'get_patient_info':          # per tutte le info su un paziente singolo 


            # richiamato da alert service

            msg = next((p for p in catalog['patients'] if p['patient_ID'] ==  params["patient_ID"]), None)  
            return json.dumps(msg)
        
        elif uri[0] == 'get_patients':              # per tutte le info su un paziente singolo 

            # richiamato da location service

            return json.dumps(catalog['patients'])
               
        elif uri[0] == 'get_doctor_info':           # per il dottore associato ad un paziente
            
            # prima trova il paziente per cui devo ricercare il medico
            patient = next((p for p in catalog['patients'] if p['patient_ID'] == params["patient_ID"] ), None) 

            # poi cerco le informazioni del medico salvate nella lista dei medici
            msg = next((d for d in catalog['doctors'] if d['doctor_ID'] == patient["doctor_ID"]), None) 

            return json.dumps(msg)

        elif uri[0] == 'avail_docs':                # Per il riempimento del menù a tendina del form registrazione paziente

            docs = catalog['doctors']
            options = {
                "fullName":[f"{doc['name']} {doc['surname']}" for doc in docs],
                "docID":[doc['doctor_ID'] for doc in docs],
                "chatID": [doc["chat_ID"]for doc in docs]
            }
        
            return json.dumps(options).encode('utf8')
        
        elif uri[0] == 'avail_devs':                # Per il riempimento del menù a tendina del form registrazione paziente

            devs = catalog['sensors_type']
            options = {
                "fullName":[dev["type"] for dev in devs],
                "devID":[dev["type_ID"] for dev in devs]
            }
        
            return json.dumps(options).encode('utf8')

        elif uri[0] == 'get_service_info':          # Per tutte ottenere le informazioni relative ad un servizio
                                            # url : 
                                            #           host:port/catalog_manager/ get_service_info ? service_ID=nomedelservizio
                                            
                                            # Restituisce l'intero dizionario relativo al servizio richiesto presente all'interno del catalog 

            return json.dumps(catalog["services"][params["service_ID"]])
        
        elif uri[0] == 'get_critical_info':         # per info su criticità sensore (solo alert x   service)

            patient = next((p for p in catalog['patients'] if p['patient_ID'] == params['patient_ID'] ), None)
            #sensor_info = next((s for s in patient["sensors"] if s['type_ID'] == params['sensor_ID'] ), None)
            return json.dumps(patient)
        
        else: 
            #cherrypyerror
            pass

    def POST(self,*uri,**params):
        
        # Estrae il catalog dal file
        with open(self.catalog_file,'r') as f:
            catalog = json.load(f)
                    
        if uri[0] == "p_rec":			#### ADD PATIENT ####

                                        # 	uri: /p_rec
                                        # 	body del post:
                                        # 		{
                                        # 			name: ,
                                        # 			surname: ,
                                        # 			chatID: ,
                                        # 			docID: ,
                                        # 			devID: 
                                        # 		})		
            
            pats=catalog["patients"]

            # Legge il body del POST richiesto da 'patient-rec.html' e lo visualizza nel terminal
            newPat=json.loads(cherrypy.request.body.read())

            # CONTROLLO DA RISCRIVERE
            # # Se il paziente è gia registrato mostra un banner di errore e indica di compiere il log-in
            # for p in pats:
            #     if (p["personal_info"]["nome"]+p["personal_info"]["cognome"]).lower == (newPat["name"]+newPat["surname"]).lower:
            #         return f"Hi {newPat['name']}, you are already registered!\nTo add a new device, please log in and follow the procedure"

            # Definisce la lista di sensori del nuovo paziente
            newPatDevs=[]
            for s in newPat["devID"]:
                newDev={
                    "type_ID": s,
                    "is_critical": "",
                    "safe_range": []
                }
                newPatDevs.append(newDev)

            # Crea un nuovo canale su ThingSpeak
            b = {
                "api_key": catalog["services"]["ThingSpeak"]["api_key"],
                "name": f"{newPat['name']} {newPat['surname']}",
                "public_flag": True
                }
            
            for i in range(len(newPatDevs)):
                b[f"field{i+1}"] = [s["type"] for s in catalog["sensors_type"] if s["type_ID"] == newPat["devID"][i]][0]
            
            # Richiesta POST per la creazione del canale su TS, e memorizzazione channel ID
            resp = json.loads(requests.post("https://api.thingspeak.com/channels.json",b).text)
            
            # Definisce la nuova scheda paziente e la inserisce nella variabile locale che rappresenta il catalog
            f_newPat={
                "patient_ID": f"p_{len(pats)+1}",
                "personal_info": {
                    "name": newPat["name"],
                    "surname": newPat["surname"],
                    "chat_ID": newPat["chatID"]
                },
                "sensors": newPatDevs,
                "TS_chID": resp["id"],
                "TS_wKey": [k["api_key"] for k in resp["api_keys"] if k["write_flag"]][0],
                "TS_rKey": [k["api_key"] for k in resp["api_keys"] if not k["write_flag"]][0],
                "doctor_ID": newPat["docID"],
                "device_connector": {
                    "service_ID": "",
                    "topic": f"service/dc_{len(pats)+1}"
                }
            }

            # Aggiorna il catalog
            catalog["patients"].append(f_newPat)

                        
            # Salva su file il catalog aggiornato
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

        elif uri[0] == "d_rec":         #### ADD DOCTOR ####

                                        # 	uri: /d_rec
                                        # 	body del post:
                                        # 		{
                                        # 			name: ,
                                        # 			surname: ,
                                        # 			chatID: 
                                        # 		})	

            docs=catalog["doctors"]

            # Legge il body del POST richiesto da 'patient-rec.html' e lo visualizza nel terminal
            newDoc=json.loads(cherrypy.request.body.read())
            
                # CONTROLLO
            # # Se il paziente è gia registrato mostra un banner di errore e indica di compiere il log-in
            # for d in docs:
            #     if (d["personal_info"]["nome"]+d["personal_info"]["cognome"]).lower == (newDoc["name"]+newDoc["surname"]).lower:
            #         return f"Hi {newDoc['name']}, you are already registered!\nPlease log in and follow the procedure"

            # Definisce la nuova scheda dottore e la inserisce nella variabile locale che rappresenta il catalog
            f_newDoc={
                "doctor_ID": f"d_{len(docs)+1}",
                "name": newDoc["name"],
                "surname": newDoc["surname"],
                "chatID" : newDoc["chatID"]
                }
            catalog["doctors"].append(f_newDoc)

            # Aggiorna 'catalog.json'
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

        elif uri[0] == "c_rec":         #### ADD CLINIC ####

                                        # 	uri: /c_rec
                                        # 	body del post:
                                        # 		{
                                        # 			name: ,
                                        # 			lon: ,
                                        # 			lat: 
                                        # 		})	

            cls=catalog["clinics"]

            # Legge il body del POST richiesto da 'patient-rec.html' e lo visualizza nel terminal
            newCls=json.loads(cherrypy.request.body.read())
            print(newCls)

                # CONTROLLO
            # # Se la clinica è gia registrata mostra un banner di errore e indica di compiere il log-in
            # for c in cls:
            #     if (c["clinic_name"]).lower == (newCls["name"]).lower:
            #         return f"Your clinic is already registered!"

            # Definisce la nuova scheda dottore e la inserisce nella variabile locale che rappresenta il catalog
            f_newCls={
                "clinic_ID": f"d_{len(cls)+1}",
                "clinic_name": newCls["name"],
                "lon": newCls["lon"],
                "lat" : newCls["lat"]
                }
            catalog["clinics"].append(f_newCls)

            # Aggiorna 'catalog.json'
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

    def PUT(self,*uri,**params):
        
        # Estrae il catalog dal file
        with open(self.catalog_file,'r') as f:
            catalog = json.load(f)

        if uri[0] == "s_up":          #### UPDATE DEVICE ####
            
                                        # 	uri: /s_up
                                        # 	body del post:
                                        # 		{
                                        # 			name: ,
                                        # 			surname: ,
                                        # 			devID: ,
                                        #           is_critical: ,
                                        #           safe_range: ["min", "max"] 

            # Legge il body del POST richiesto da 'patient-rec.html' e lo visualizza nel terminal
            devInfo=json.loads(cherrypy.request.body.read())

            # Individua il paziente 
            patInd = 0
            for pat in catalog["patients"]:    
                if  pat["personal_info"]["name"]+pat["personal_info"]["surname"] == devInfo["name"]+devInfo["surname"]:
                    break
                patInd+=1
            pat = catalog["patients"][patInd]
            
            # Individua il sensore
            devInd = 0
            for dev in pat["sensors"]:
                if dev["type_ID"] == devInfo["devID"]:
                    break
                devInd+=1
            dev = pat["sensors"][devInd]

            # Applica l'aggiornamento alla scheda sensore
            dev["is_critical"] = devInfo["is_critical"]
            dev["safe_range"] = [float(val) for val in devInfo["safe_range"]]

            # Aggiorna il catalog
            catalog["patients"][patInd]["sensors"][devInd] = dev
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)


#####################################################################################################


if __name__ == '__main__':

    catalog_file = 'catalog.json'

                               
    with open('config.json','r') as f:                                               
        cat = json.load(f)                                                    
    host = cat["base_host"]                                                        
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["address"]

    print(catalog_address)
    # with open("./config.json",'r') as f:
    #   catalog_address = json.load(f)["catalog_address"]
    
    with open('catalog.json','r') as f:
                front_info = json.load(f)['services']['front_end']

    conf = {
        '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tool.session.on': True,
                'tools.response_headers.on': True,
                'tools.response_headers.headers': [('Access-Control-Allow-Origin', f"http://{front_info['host']}:{front_info['port']}")],
        }
    }

    cherrypy.tree.mount(catalog(catalog_file), '/catalog_manager', conf)
      
    cherrypy.config.update({'server.socket_host': host,
                            'server.socket_port': int(port)})
    # this is needed if you want to have the custom error page
    # cherrypy.config.update({'error_page.400': error_page_400}) # potremmo metterla anche noi questa pagina
    cherrypy.engine.start()
    cherrypy.engine.block()