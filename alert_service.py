# subscriber a dati 
import json
import time

from numpy import empty
import MQTT
import requests as r

# nota: magari si potrebbe anche mandare alla clinica il numero di telefono nel messaggio, così che possano verificare che non ci sia un errore nei sensori o qualcosa di simile 
# e non mandino qualcuno o si attivino inutilmente

# si potrebbe anche aggiungere un controllo su dati successivi, del tipo che se ce ne sono 5 fuori range di fila si attiva
    
class data_analysis_service():
    def __init__(self, broker, port, ID, topic,catalog_address,location_service):
        self.alert_service = MQTT((broker, port, ID, self))
        self.alert_service.start()
        self.alert_service.my_subscribe(topic)
        self.catalog_address = catalog_address # tutti gli indirizzi si potrebbero salvare nel catalog e prenderli all'inizio con una richiwsta e poi aggiungere un controllo negli errori nel caso 
        self.location_service = location_service

    def notify(self, topic, msg): # controllare come funziona MQTT

        patient_ID = msg['p_id'] # ricontrollare come funzionano i messaggi e fare il punto su come strutturarli 
        measures = msg['measures']


        for measure in measures:    #controlla le misure, posso aggiungere tutte quelle che voglio 
            if measure['n'] =='bpm':
                if True:    # da aggiungere la condizione qui 
                    # 
                    msg = 'fuori range di questo'
                    stato = self.alert(patient_ID,msg) # a questo punto chiamo la funzione alert (basta richiamarlo ogni volta)
                    return stato
                    
            elif measure['n'] =='glucosimetro': 
                pass # sarebbe come sopra

            elif measure['n'] =='qualcos altro':
                pass

    def alert(self,patient_ID):
        #r.get('location service','location ')

        doctor = r.get(self.catalog_address + 'get_doctor',data = {"p_ID":patient_ID})

        print("attenzioneeee" + patient_ID + " sta morendo")

        #manda un messaggio al doctor (bisogna decidere come si comunica con lui)

        nearest_clinic = r.get(self.location_service, data = {"p_ID":patient_ID})
        
        if nearest_clinic['nearest']: 

             #manda messaggio (bisogna decidere come la clinica comunica)

            return 'messaggio mandato correttamente'
        else: 
            return 'errore, non si conosce la posizione del paziente' # in questo caso manda sol un messaggio la medico



if __name__ =='__main__':
    dati = json.load(open('settings_as.json','r')) # idea -> settings contiene tutte le impostazioni per i microservices in un dizionario 
    # le impostazioni si potrebber anche mettere nel catalo e prenderle con un get invece di caricarle con settings e mettere solo il catalog come service
    dati = dati['location_service']

    topic = dati['topic']
    broker = dati['broker']
    port = dati['port']
    service_ID = dati['ID']
    service =  data_analysis_service(broker, port, service_ID, topic)

    done = False
    while not done:
        #mettere condizione di stop?
        time.sleep(1)