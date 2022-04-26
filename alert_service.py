# subscriber a dati 
import json
import time

from numpy import empty
from MQTT import *
import requests as r

from location_service import location_service

# nota: magari si potrebbe anche mandare alla clinica il numero di telefono nel messaggio, così che possano verificare che non ci sia un errore nei sensori o qualcosa di simile 
# e non mandino qualcuno o si attivino inutilmente

# si potrebbe anche aggiungere un controllo su dati successivi, del tipo che se ce ne sono 5 fuori range di fila si attiva
    
class alert_service:
    def __init__(self, broker, port, ID, topic,catalog_address,location_service):
        self.alert_service = MQTT(ID, broker, port, self)
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
                    problem = 'fuori range di questo'
                    stato = self.alert(patient_ID,problem) # a questo punto chiamo la funzione alert (basta richiamarlo ogni volta)
                    print(stato)
                    
            elif measure['n'] =='glucosimetro': 
                pass # sarebbe come sopra

            elif measure['n'] =='qualcos altro':
                pass

    def alert(self,patient_ID,problem):

        doctor = r.get(self.catalog_address + 'get_doctor',data = {"p_ID":patient_ID})

        # implementare una funzioe per mandare il messaggio al doctor
        print("attenzioneeee" + patient_ID + " sta morendo")

        
        nearest_clinic = r.get(self.location_service, data = {"p_ID":patient_ID})

        topic = nearest_clinic["clinic_address"]

        if nearest_clinic['nearest']:    
            
            msg = {
                "p_ID":patient_ID,
                "latitudine":nearest_clinic['patient_pos']['longitudine'],
                "longitudide":nearest_clinic['patient_pos']['latitudine'],
                "problema":problem,
                "doctor contact":"" # da completare
            }
            self.alert_service.my_publish(topic, msg)
            return 'messaggio mandato correttamente'
        else: 
            return 'errore, non si conosce la posizione del paziente' # in questo caso manda solo un messaggio la medico (non è)



if __name__ =='__main__':
    dati = json.load(open('settings_as.json','r')) # idea -> settings contiene tutte le impostazioni per i microservices in un dizionario 
    # le impostazioni si potrebber anche mettere nel catalog e prenderle con un get invece di caricarle con settings e mettere solo il catalog come service
    location = dati['location_address']
    catalog = dati['catalog_address']
    topic = dati['topic']
    broker = dati['broker']
    port = dati['port']
    service_ID = dati['service_ID']
    service =  alert_service(broker, port, service_ID, topic,location, catalog)

    done = False
    while not done:
        #mettere condizione di stop?
        time.sleep(1)