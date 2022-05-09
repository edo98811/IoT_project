import json
import requests
import cherrypy
from pprint import pprint

# va aggiunto un controllo params in tutte le funzioni del codice

# nell'uri metto solo il tipo di richiesta (quindi da chi viene) 
# ma devo tenere conto che c'è anche la prima parte dell'indirizzo 

# importante far quadrare tutti i nomi di tutti 

class catalog():
    exposed=True

    def __init__(self,catalog_file):
        self.catalog_file = catalog_file

    def GET(self,*uri,**params): 

        # Lettura del catalog
        with open(self.catalog_file,'r') as f:
            catalog = json.load(f)

        # device connector info per avviarsi 
        if uri[0] == 'get_dc_info':

            p_ID = params['p_ID'] #cercare le info di un paziente conoscendo il suo ID, aggiungere try except magari 
            # vediamo se funziona
            pat = next((p for p in catalog['patients'] if p['patient_ID'] == p_ID ), None) # questa funzione crea un iterator della lista (un oggetto sostanzialmente che applica una funzione a qualche altro oggetto, in questo caso applica un controllo ad una lista)

            msg = {
                "broker":catalog["services"]["MQTT"]["broker"],
                "port":catalog["services"]["MQTT"]["port"],
                "topic":pat["device_connector"]["topic"],
            }
            return json.dumps(msg)

        #sensori relativi ad un paziente
        elif uri[0] == 'get_sensors':

            p_ID = params['p_ID']

            # Estrazione scheda paziente di interesse
            pat = next((p for p in catalog['patients'] if p['patient_ID'] == p_ID ), None)

            # Estrazione scheda sensori del paziente
            sensors = pat["sensors"]
            sensor_list = []

            # Creazione lista delle tipologie di sensori possedute dal paziente
            for sensor in sensors:
                sensor_list.append({
                    "type": sensor["sensor_type"],
                    "ID": sensor["sensor_ID"]
                    }
                )
                
            return json.dumps(sensor_list)

        
        elif uri[0] == 'sensor-general-info':   # per passare al DC le info sulle tipologie di sensori
                                                # url : host:port/catalog_manager/sensor-general-info?type=typeID
                                                #         
            # Estrae dal catalog la scheda sensore associata all'ID passato nei parametri
            type = params["type"]
            sen = [s for s in catalog['sensors_type'] if s['type_ID'] == type][0] 
            # viene costruito come una lista con un solo elemento, quindi lo estraggo con ...[0] 

            return json.dumps(sen)

        #funzione per le cliniche
        elif uri[0] == 'get_clinics':

            clinics = catalog["clinics"]

            return json.dumps(clinics)

        #per tutti i pazienti 
        elif uri[0] == 'get_patients':

            return json.dumps(catalog['patients'])

        #per il dottore di un paziente
        elif uri[0] == 'get_doctor':

            p_ID = params["p_ID"] 
            patient = next((p for p in catalog['patients'] if p['patient_ID'] == p_ID), None) # c'è un modo migliore per farlo l'avevo visto su internet
            d_ID = patient["doctor_ID"]
            doctor = next((d for d in catalog['doctors'] if d['doctor_ID'] == d_ID), None) # questa funzione crea un iterator della lista (un oggetto sostanzialmente che applica una funzione a qualche altro oggetto, in questo caso applica un controllo ad una lista)

            return json.dumps(doctor['address']) # se serve un campo in particolare
    
        elif uri[0] == 'avail-docs':    # Per il riempimento del menù a tendina del form registrazione paziente

            docs = catalog['doctors']
            options = {
                "fullName":[f"{doc['name']} {doc['surname']}" for doc in docs],
                "docID":[doc['doctor_ID'] for doc in docs],
                "chatID":[doc['chatID'] for doc in docs]
            }
        
            return json.dumps(options).encode('utf8')
        
        elif uri[0] == 'avail-devs':    # Per il riempimento del menù a tendina del form registrazione paziente

            devs = catalog['sensors_type']
            options = {
                "fullName":[dev["type"] for dev in devs],
                "devID":[dev["type_ID"] for dev in devs]
            }
        
            return json.dumps(options).encode('utf8')

        elif uri[0] == 'service-address':   # Per ottenere l'indirizzo di un certo servizio REST
                                            # url : host:port/catalog_manager/service-address?name=nomedelservizio

            # Costruisce la stringa da passare in risposta, contenente l'indirizzo del servizio richiesto
            serviceAddress = "http://"+catalog["base_host"]+":"+catalog["base_port"]+catalog["services"][params["name"]]["address"]

            return serviceAddress
        
        elif uri[0] == 'service-info':  # Per ottenere le informzioni relative ad un servizio (tutto il dizionario)
                                        # url : host:port/catalog_manager/service-info?name=nomedelservizio

            return json.dumps(catalog["services"][params["name"]])

        else: 
            #cherrypyerror
            pass

    def POST(self,*uri,**params):
        
        # Estrae il catalog dal file
        with open(self.catalog_file,'r') as f:
            catalog = json.load(f)
                    
        if uri[0] == "p-rec":			#### ADD PATIENT ####

                                        # 	uri: /p-rec
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
            pprint(newPat)

            # CONTROLLO DA RISCRIVERE
            # # Se il paziente è gia registrato mostra un banner di errore e indica di compiere il log-in
            # for p in pats:
            #     if (p["personal_info"]["nome"]+p["personal_info"]["cognome"]).lower == (newPat["name"]+newPat["surname"]).lower:
            #         return f"Hi {newPat['name']}, you are already registered!\nTo add a new device, please log in and follow the procedure"

            # Definisce la lista di sensori del nuovo paziente
            newPatDevs=[];i=0
            for s in newPat["devID"]:
                i+=1
                newDev={
                    "sensor_ID": f"p_{len(pats)+1}_{i}",
                    "sensor_type": s,
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
            
            # Richiesta POST per la creazione del canale su TS, e memorizzazion channel ID
            resp = json.loads(requests.post("https://api.thingspeak.com/channels.json",b).text)

            pprint(resp)
            
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
                    "topic": f"service/dc_{len(pats)+1}"
                }
            }

            catalog["patients"].append(f_newPat)

                        
            # Aggiorna 'catalog.json'
            with open(self.catalog_file,'w') as f:
                json.dump(catalog,f,indent=4)

        elif uri[0] == "d-rec":         #### ADD DOCTOR ####

                                        # 	uri: /d-rec
                                        # 	body del post:
                                        # 		{
                                        # 			name: ,
                                        # 			surname: ,
                                        # 			chatID: 
                                        # 		})	

            docs=catalog["doctors"]

            # Legge il body del POST richiesto da 'patient-rec.html' e lo visualizza nel terminal
            newDoc=json.loads(cherrypy.request.body.read())
            pprint(newDoc)
            
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

        elif uri[0] == "c-rec":         #### ADD CLINIC ####

                                        # 	uri: /c-rec
                                        # 	body del post:
                                        # 		{
                                        # 			name: ,
                                        # 			lon: ,
                                        # 			lat: 
                                        # 		})	

            cls=catalog["clinics"]

            # Legge il body del POST richiesto da 'patient-rec.html' e lo visualizza nel terminal
            newCls=json.loads(cherrypy.request.body.read())
            pprint(newCls)

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
            
        elif uri[0] == "s-up":          #### UPDATE DEVICE ####
            
                                        # 	uri: /s-up
                                        # 	body del post:
                                        # 		{
                                        # 			name: ,
                                        # 			surname: ,
                                        # 			devID: ,
                                        #           is_critical: ,
                                        #           safe_range: ["min", "max"] 

            # Legge il body del POST richiesto da 'patient-rec.html' e lo visualizza nel terminal
            devInfo=json.loads(cherrypy.request.body.read())
            pprint(devInfo)

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
                if dev["sensor_type"] == devInfo["devID"]:
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

            
                    
#deve rispondere a: location, data analysis,alert e altre? serve importare le librerie nelle classi ? 
