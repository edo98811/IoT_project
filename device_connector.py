import random
from MyMQTT import *
from MQTT import *
import random
import requests
import json 
import time

#@cherrypy.tools.json_out() per rispondere e avere come return un json 
# questa classse serve per creare gli oggetti sensore, ipotizzo che funzionino tutti allo stesso modo cioè generando un valore casuale all'interno del range ogni volta he viene richiesto


# creare una classe apposta per il gps? pensare ad un modo più intelligente per simulare un gps
class sensor_def():
    def __init__(self, sensor_type, sensor_ID, range, unit ):
        self.sensor_type = sensor_type
        self.sensor_ID = sensor_ID
        self.range = range 
        self.unit = unit

    def get_reading(self):
        output = random.randint(self.range[0],self.range[1])
        return output


class device_connector():
    def __init__(self, broker, port, patient_ID, topic,catalog_address):

        #self.catalog_address = catalog_address non serve
        self.dc = MQTT(patient_ID, broker, port, self)
        self.topic = topic
        self.dc.start()
        self.basetime = time.time()
        self._message = {			
            'p_ID':patient_ID,
            't':self.basetime,
            'e':[]
			}

        self._sensors = []

        sensors = json.loads(requests.get(catalog_address + '/get_sensors',params= {'p_ID':patient_ID}).text)#chiede la lista dei sensori del patient id che gli passo  

        for sensor in sensors['sl']:

            sensor = sensor_def(sensor['sensor_type'],sensor['sensor_ID'],sensor['range'],sensor['unit'])
            self._sensors.append(sensor)

            self._message['e'].append({ # creo un template del messaggio del sensore
                'n':sensor.sensor_ID,
                'vs':sensor.sensor_type,
                'v':'',
                #'t':time.time()-self.basetime, non serve direi
                'u':sensor.unit
            })

    def get_readings(self): 

        for n,sensor in enumerate(self._sensors):

            value = sensor.get_reading() #questo get reading prende un valore di lettura dal sensore
            self.message = self._message #copia il template
            self.message['e'][n]['v'] = value
        print("sensori funzionanti")
        self.message['t'] = time.time()-self.basetime 

        
    def send(self):
        self.dc.my_publish(self.topic, self.message) #pubblica il template nel topic corretto poi cancella il messaggio 
        del self.message


if __name__ == '__main__':
    
    catalog_address = 'http://127.0.0.1:8080/catalog_manager'
    patient_ID = 'p_1'
    pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,params= {"p_ID":patient_ID}).text) #manda una richiesta al catalog
    print(pat_info)
    device_connector1 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"],catalog_address)

    patient_ID = 'p_2'
    print(pat_info)
    pat_info = json.loads(requests.get(catalog_address + '/get_dc_info' ,params = {"p_ID":patient_ID}).text)

    device_connector2 = device_connector(pat_info["broker"], pat_info["port"], patient_ID, pat_info["topic"], catalog_address)

    while True:
        time.sleep(2)
        device_connector1.get_readings()
        device_connector1.send()
        device_connector2.get_readings()
        device_connector2.send()
