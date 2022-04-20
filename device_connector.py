import random
import MQTT
import random
import requests
import json 
import time

#@cherrypy.tools.json_out() per riapondere e avere come return un json 

# creare una classe apposta per il gps? pensare ad un modo più intelligente per simulare un gps
class sensor_def():
    def __init__(self, sensor_type, sensor_ID, range, unit ):
        self.sensor_type = sensor_type
        self.sensor_ID = sensor_ID
        self.range = range 
        self.unit = unit

    def get_reading(self):
        output = random.randint(self.range(0),self.range(1))
        return output


class device_connector():
    def __init__(self, broker, port, patient_ID, topic,catalog_address):

        #self.catalog_address = catalog_address non serve
        self.dc = MQTT(broker, port, patient_ID, self)
        self.topic = topic
        self.dc.start()
        self._message = {			
            'p_ID':patient_ID,#sicuro che è giusto, bisogna capire come aggiungere il basetime o comunque forse implemetare questo tipo di calcolo nel data processing
            't':0,
            'e':[]
			}

        self._sensors = []

        sensors = requests.get(catalog_address + '/get_sensors',data = {'p_ID':patient_ID})#chiede la lista dei sensori del patient id che gli passo  

        for sensor in sensors:

            self._sensors.append(sensor_def(sensor['sensor_type'],sensor['sensor_ID'],sensor['range'],sensor['unit']))

            self._message['e'].append({ # creo un template del messaggio del sensore
                'n':sensor['sensor_ID'],
                'vs':sensor['sensor_type'],
                'v':'',
                't':'',
                'u':sensor["unit"]
            })

    def get_readings(self): 

        for sensor,n in enumerate(self._sensors): #magari va capito meglio come fare questa parte, cioè come migliorare il fatto che i messaggi debbano essere in tempo reale

            value = sensor.get_reading() #questo get reading fa il lavoro che dovrebbe fare il senosre cioè prende un valore di lettura
            self.message = self._message #copia il template
            self.message['e'][n]['v'] = value # sicuro che si farebbe così? comuque questo mette il valore letto nel messaggio 

        self.message['t'] = time.time() # bisognerebbe sottrarre il base time

        
    def send(self):
        self.dc.my_publish(self.topic, self.message) #pubblica il template nel topic corretto poi cancella il messaggio 
        del self.message


if __name__ == '__main__':
    
    catalog_address = '127.0.0.1/catalog_manager'
    #capire bene come strutturare questa parte qui (prendere dal sensor_type il sensore)
    patient_ID = 1
    pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,data = {"p_ID":patient_ID})) #manda una richiesta al catalog (poi posso togliere json.loads forse)
    device_connector1 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"],catalog_address)

    patient_ID = 2
    pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,data = {"p_ID":patient_ID}))
    device_connector2 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"], catalog_address)

    while True:

        device_connector1.get_readings()
        device_connector1.send()
        device_connector2.get_readings()
        device_connector2.send()

        #l'altra idea sarebbe stata avere un comando per ogni sensore
        # device_connector1.post('1',random.randomint())
        # device_connector1.post('2',random.rand())
        # device_connector1.post('3',random.rand())
        # device_connector1.post('4',random.rand())
        # device_connector1.send()

        # device_connector2.post('6',random.rand())
        # device_connector2.post('7',random.rand())
        # device_connector2.post('8',random.rand())
        # device_connector2.send()