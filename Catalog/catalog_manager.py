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
            try:
                patient = next((p for p in catalog['patients'] if p['patient_ID'] == params['patient_ID'] ), None) 
            except:
                raise cherrypy.HTTPError(500, f"invalid parameter sent, patient not registered")

            msg = {
                "broker":catalog["services"]["MQTT"]["broker"],
                "port":catalog["services"]["MQTT"]["port"],
                "topic":f'{catalog["services"]["MQTT"]["baseTopic"]}/{patient["device_connector"]["topic"]}'
            }

            return json.dumps(msg)

        elif uri[0] == 'get_sensors':               # per sensori relativi ad un paziente

            # richiamato da device connector
          
            # prende le info del paziente a recupera la lista dei sensori
            try:
                patient = next((p for p in catalog['patients'] if p['patient_ID'] == params['patient_ID'] ), None)
            except: 
                raise cherrypy.HTTPError(500, f"invalid parameter sent, patient not registered")

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
                    "unit":s_type["unit"],
                    "over_safe":s_info["over_safe"],
                    "under_safe":s_info["under_safe"]
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
            try:
                msg = next((p for p in catalog['patients'] if p['patient_ID'] ==  params["patient_ID"]), None)  
            except: 
                raise cherrypy.HTTPError(500, f"invalid parameter sent, patient not registered")

        
            return json.dumps(msg)
        
        elif uri[0] == 'get_patients':              # per tutte le info su un paziente singolo 

            # richiamato da location service

            return json.dumps(catalog['patients'])
               
        elif uri[0] == 'get_doctor_info':           # per il dottore associato ad un paziente
            
            # prima trova il paziente per cui devo ricercare il medico
            try:
                patient = next((p for p in catalog['patients'] if p['patient_ID'] == params["patient_ID"] ), None)
            except: 
                raise cherrypy.HTTPError(500, f"invalid parameter sent, patient not registered")


            # poi cerco le informazioni del medico salvate nella lista dei medici
            try:
                msg = next((d for d in catalog['doctors'] if d['doctor_ID'] == patient["doctor_ID"]), None) 
            except: 
                raise cherrypy.HTTPError(500, f"patient's doctor not registered")

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
            raise cherrypy.HTTPError(500, f"{uri[0]} it is not an available command")

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

            # Se il paziente è gia registrato mostra un messaggio di errore
            for p in pats:
                if (p["personal_info"]["name"]+p["personal_info"]["surname"]).lower() == (newPat["name"]+newPat["surname"]).lower():
                    return json.dumps({"text": f"{newPat['name']} {newPat['surname']} was already registered"})

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
            if pats:
                newID = int(pats[-1]['patient_ID'].split('_')[-1])+1
            else:
                newID = 1
            
            f_newPat={
                "patient_ID": f"p_{newID}",
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
                    "topic": f"service/dc_{int(pats[-1]['patient_ID'].split('_')[-1])+1}"
                }
            }

            # Aggiorna il catalog
            catalog["patients"].append(f_newPat)

                        
            # Salva su file il catalog aggiornato
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

            return json.dumps({"text": f"Patient {newPat['name']} {newPat['surname']} successfully registered!"})

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
            
            # Se il medico è gia registrato mostra un messaggio di errore
            for d in docs:
                if (d["name"]+d["surname"]).lower() == (newDoc["name"]+newDoc["surname"]).lower():
                    return json.dumps({"text": f"{newDoc['name']} {newDoc['surname']} is already registered"})

            # Definisce la nuova scheda dottore e la inserisce nella variabile locale che rappresenta il catalog
            if docs:
                newID = int(docs[-1]['doctor_ID'].split('_')[-1])+1
            else:
                newID = 1

            f_newDoc={
                "doctor_ID": f"d_{newID}",
                "name": newDoc["name"],
                "surname": newDoc["surname"],
                "chatID" : newDoc["chatID"]
                }
            catalog["doctors"].append(f_newDoc)

            # Aggiorna 'catalog.json'
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

            return json.dumps({"text": f"Doctor {newDoc['name']} {newDoc['surname']} successfully registered!"})

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

            # Se la clinica è gia registrata mostra un messaggio di errore
            for c in cls:
                if c["name"].lower() == newCls["name"].lower():
                    return json.dumps({"text": f"Clinic {newCls['name']} was already registered"})

            # Definisce la nuova scheda clinics e la inserisce nella variabile locale che rappresenta il catalog
            if cls:
                newID = int(cls[-1]['clinic_ID'].split('_')[-1])+1
            else:
                newID = 1

            f_newCls={
                "clinic_ID": f"cl_{newID}",
                "name": newCls["name"],
                "location":{
                    "longitude": newCls["lon"],
                    "latitude" : newCls["lat"]
                },
                "clinic_topic": f"alert/cl_{newID}"
            }
            catalog["clinics"].append(f_newCls)

            # Aggiorna 'catalog.json'
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

            return json.dumps({"text": f"Clinic {newCls['name']} successfully registered! (Clinic ID: {f_newCls['clinic_ID']})"})

        elif uri[0] == "s_rec":         #### ADD SENSOR ####

            sensors = catalog['sensors_type']

            # Legge il body del POST richiesto da 'dev-rec.html'
            newSen=json.loads(cherrypy.request.body.read())

            # Definisce la nuova scheda sensore e la inserisce nella variabile locale che rappresenta il catalog
            if sensors:
                newID = int(sensors[-1]['type_ID'].split('_')[-1])+1
            else:
                newID = 1

            f_newSen={
                "type_ID": f"s_{newID}",
                "type": newSen["type"],
                "range": newSen["range"],
                "unit": newSen["unit"]
                }

            catalog["sensors_type"].append(f_newSen)

            # Aggiorna 'catalog.json'
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)
            
            return json.dumps({"text": f"Sensor {newSen['type']} successfully registered!"})

        else: 
            raise cherrypy.HTTPError(500, f"{uri[0]} it is not an available command")

    def DELETE(self, *uri, **params):

        # Estrae il catalog dal file
        with open(self.catalog_file,'r') as f:
            catalog = json.load(f)

        if uri[0] == "p_del":           #### DELETE PATIENT ####

                                        # 	uri: /p_del
                                        # 	body del post:
                                        # 		{
                                        # 			name: ,
                                        # 			surname: 
                                        # 		})
            
            pats = catalog["patients"]
            body = json.loads(cherrypy.request.body.read())

            # Controllo sulla correttezza del nome inserito
            i = -1
            for n,p in enumerate(pats):
                if p['personal_info']['name']+p['personal_info']['surname'] == body['name']+body['surname']:
                    i = n
            if i == -1:
                return json.dumps({"text": f"There is no patient named '{body['name']} {body['surname']}' in the system"})
            
            pat2del = pats[i]
            
            chan2del = pat2del['TS_chID']
            APIkey = catalog['services']['ThingSpeak']['api_key']

            # Eliminazione della scheda paziente
            pats.pop(i) 

            # Eliminazione canale TS
            TS_uri = catalog['services']['ThingSpeak']['url_delete_channel'].split('/')
            TS_uri[-1] = f"{chan2del}.json"
            url = '/'.join(TS_uri)
            resp = requests.delete(url,json={'api_key':APIkey})
            if int(resp.status_code) != 200:
                return json.dumps({"text": f"A problem occurred contacting Thingspeak during patient {body['name']} {body['surname']} unsubscription!"})


            # Aggiorna il catalog
            catalog["patients"] = pats

                        
            # Salva su file il catalog aggiornato
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

            return json.dumps({"text": f"Patient {body['name']} {body['surname']} successfully removed from the system!"})

        elif uri[0] == "d_del":         #### DELETE DOCTOR ####
        
                                        # 	uri: /d_del
                                        # 	body del post:
                                        # 		{
                                        # 			name: ,
                                        # 			surname: 
                                        # 		})
            
            docs = catalog['doctors']
            body = json.loads(cherrypy.request.body.read())

            # Controllo sulla correttezza del nome inserito
            i = -1
            for n,d in enumerate(docs):
                if d['name']+d['surname'] == body['name']+body['surname']:
                    i = n
            if i == -1:
                return json.dumps({"text": f"There is no doctor named '{body['name']} {body['surname']}' in the system"})
            

            doc2del = docs[i]

            docID = doc2del['doctor_ID']

            pats = catalog['patients']
            stillPats = [p for p in pats if p['doctor_ID'] == docID]

            if stillPats:
                msg = f"Doctor {body['name']} {body['surname']} has some patients still registered to the system:<br>"
                for p in stillPats:
                    msg += f"{p['personal_info']['name']} {p['personal_info']['surname']}<br>"
                msg += "<br>Once these patients will be unsubscribed, the doctor will be able to unsubscribe too"
                return json.dumps({"text": msg})

            else:
                docs.pop(i)
            
            # Aggiorna il catalog
            catalog["doctors"] = docs
                        
            # Salva su file il catalog aggiornato
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

            return json.dumps({"text": f"Doctor {body['name']} {body['surname']} successfully unsubscribed!"})

        elif uri[0] == "c_del":         #### DELETE CLINIC ####

                                        # 	uri: /c_del
                                        # 	body del post:
                                        # 		{
                                        # 			name: 
                                        # 		})
                    
            cls = catalog['clinics']
            body = {}
            body['name'] = uri[1]

             # Controllo sulla correttezza del nome inserito
            i = -1
            for n,c in enumerate(cls):
                if c['name'] == body['name']:
                    i = n
            if i == -1:
                return json.dumps({"text": f"There is no clinic named '{body['name']} {body['surname']}' in the system"})
            
            cls.pop(i)

            # Aggiorna il catalog
            catalog["clinics"] = cls
                        
            # Salva su file il catalog aggiornato
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

            return json.dumps({"text": f"Clinic {body['name']} successfully unsubscribed!"})

        else: 
            raise cherrypy.HTTPError(500, f"{uri[0]} it is not an available command")

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
                                        #           safe_range: ["min", "max"],
                                        #           over_safe: ,
                                        #           under_safe:
                                        #       }

            # Legge il body del POST richiesto da 'patient-rec.html'
            devInfo=json.loads(cherrypy.request.body.read())

            # Controllo sulla correttezza del nome inserito
            i = -1
            for n,p in enumerate(catalog['patients']):
                if p['personal_info']['name']+p['personal_info']['surname'] == devInfo['name']+devInfo['surname']:
                    i = n
            if i == -1:
                return json.dumps({"text": f"There is no patient named '{devInfo['name']} {devInfo['surname']}' in the system"})
            
            pat = catalog["patients"][i]

            # Individua il sensore
            devInd = 0
            notFound = True
            for dev in pat["sensors"]:
                if dev["type_ID"] == devInfo["devID"]:
                    notFound = False
                    break
                devInd+=1
            
            # Controllo sulla correttezza del sensore selezionato
            if notFound:
                return json.dumps({"text": f"Patient {devInfo['name']} {devInfo['surname']} does not have the selected device"})
            
            dev = pat["sensors"][devInd]

            # Applica l'aggiornamento alla scheda sensore
            dev["is_critical"] = devInfo["is_critical"]
            dev["safe_range"] = [float(val) for val in devInfo["safe_range"]]
            dev["over_safe"] = devInfo["over_safe"]
            dev["under_safe"] = devInfo["under_safe"]

            # Aggiorna il catalog
            catalog["patients"][i]["sensors"][devInd] = dev
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

            return json.dumps({"text": f"Device information successfully updated!"})
        else: 
            raise cherrypy.HTTPError(500, f"{uri[0]} it is not an available command")
            
#####################################################################################################


if __name__ == '__main__':

    catalog_file = 'catalog.json'

                               
    with open('config.json','r') as f:                                               
        cat = json.load(f)                                                    
    host = cat["base_host"]                                                        
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["address"]
    
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