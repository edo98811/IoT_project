import json
#import requests
#import cherrypy

# va aggiunto un controllo params in tutte le funzioni del codice
# nell'uri metto solo il tipo di richiesta (quindi da chi iene) ma devo tenere conto che c'è anche la prima parte dell'indirizzo 
# importante far quadrare tutti i nomi di tutti 

class catalog():
    exposed=True
    def __init__(self,catalog_file):
        self.catalog_file = catalog_file

    def GET(self,*uri,**params): # come funzionano questi parametri?

        # device connector info per avviarsi 
        if uri[0] == 'get_dc_info':

            catalog = json.load(open(self.catalog_file,'r'))
            p_ID = params['p_ID'] #cercare le info di un paziente conoscendo il suo ID, aggiungere try except magari 
            # vediamo se funziona
            pat = next((p for p in catalog['patients'] if p['patient_ID'] == p_ID ), None) # questa funzione crea un iterator della lista (un oggetto sostanzialmente che applica una funzione a qualche altro oggetto, in questo caso applica un controllo ad una lista)

            msg = {
                "broker":pat["device_connector"]["broker"],
                "port":pat["device_connector"]["port"],
                "topic":pat["device_connector"]["topic"],
            }
            return json.dumps(msg)

        #sensori elativi ad un paziente
        elif uri[0] == 'get_sensors':

            catalog = json.load(open(self.catalog_file,'r'))


            p_ID = params['p_ID']
          
            pat = next((p for p in catalog['patients'] if p['p_ID'] == p_ID ), None) #sempre solito metodo di iterazione
            sensor_ids = pat["sensors"]
            sensor_list = []

            for sensor_id in sensor_ids:

                # questa funzione crea un iterator della lista (un oggetto sostanzialmente che applica una funzione a qualche altro oggetto, in questo caso applica un controllo ad una lista)
                sensor_list.append(next((s for s in catalog['sensors'] if s['s_ID'] == sensor_id ), None))
                # va ok perchè in ogni caso ce ne dobbe essere solo uno di sensore, quindi l'output è un elemento solo e lo aggiunge alla lista

            return json.dumps(sensor_list)


        #funzione per le cliniche
        elif uri[0] == 'get_clinics':

            catalog = json.load(open(self.catalog_file,'r'))

            clinics = catalog["clinics"]

            return json.dumps(clinics)

        #per tutti i pazienti 
        elif uri[0] == 'get_patients':
            catalog = json.load(open(self.catalog_file,'r'))

            return json.dumps(catalog['patients'])

        #per il dottore di un paziente
        elif uri[0] == 'get_doctor':

            catalog = json.load(open(self.catalog_file,'r'))

            p_ID = params["p_ID"] 
            patient = next((p for p in catalog['patients'] if p['patient_ID'] == p_ID), None) # c'è un modo migliore per farlo l'avevo visto su internet
            d_ID = patient["doctor_ID"]
            doctor = next((d for d in catalog['doctors'] if d['doctor_ID'] == d_ID), None) # questa funzione crea un iterator della lista (un oggetto sostanzialmente che applica una funzione a qualche altro oggetto, in questo caso applica un controllo ad una lista)

            return json.dumps(doctor['address']) # se serve un campo in particolare
	
	else: 
		#cherrypyerror
		pass

	def POST(self,*uri,**params):
	
	# Estrae il catalog dal file
	f=open(self.catalog_file,'r')
	catalog = json.load(f)
	f.close		

	if uri[0] == "p-rec":			#### ADD PATIENT ####	
									# 	uri: /p-rec
									# 	body del post:
									# 		{
									# 			name: ,
									# 			surname: ,
									# 			chatID: ,
									# 			docName: ,
									# 			docSurname: ,
									# 			dev: 
									# 		})		
		
		pats=catalog["patients"]
		docs=catalog["doctors"]
		sens=catalog["sensors"]

		# Legge il body del POST richiesto da 'patient-rec.html' e lo visualizza nel terminal
		newPat=json.loads(cherrypy.request.body.read())
		pprint(newPat)

		# Se il paziente è gia registrato mostra un banner di errore e indica di compiere il log-in
		for p in pats:
			if (p["personal_info"]["nome"]+p["personal_info"]["cognome"]).lower == (newPat["name"]+newPat["surname"]).lower:
				return f"Hi {newPat['name']}, you are already registered!\nTo add a new device, please log in and follow the procedure"
		
		# Individua l'ID del medico curante del nuovo paziente
		for d in docs:
			if (d["name"]+d["surname"]).lower == (newPat["docName"]+newPat["docSurname"]).lower:
				docID = d["doctor_ID"]
			else:
				docID=f"d_{len(docs)+1}"
		

		# Individua l'ID dei sensori posseduti dal paziente tra quelli presenti nel catalog
		devID=[]
		for d_newPat in newPat["dev"]:
			for s in sens:					
				if s["sensor_type"] == d_newPat:
					devID.append(s["sensor_ID"])

		# Definisce la nuova scheda paziente e la inserisce nella variabile locale che rappresenta il catalog
		f_newPat={
			"patient_ID": f"p_{len(pats)+1}",
			"personal_info": {
				"nome": newPat["name"],
				"cognome": newPat["surname"],
				"malattia": ""
			},
			"sensors": devID,
			"doctor_ID": docID,
			"device_connector": {
				"broker": "",
				"port": "",
				"id": "",
				"topic":""
			}
		}

		catalog["patients"].append(f_newPat)

		# Aggiorna 'catalog.json'
		f=open(self.catalog_file,'w')
		json.dump(catalog,f,indent=4)
		f.close()

		return f"Registration succeeded!\nWelcome {newPat['name']}"



	pass
	#addsensor
	#addpatient
	#adddoctor
	#addclinic

#deve rispondere a: location, data analysis,alert e altre? serve importare le librerie nelle classi ? 
