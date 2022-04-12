import random
import MQTT
import random
import requests
import json 

class sensor_def():
    def __init__(self, sensor_type, sensor_ID, range):
        self.sensor_type = sensor_type
        self.sensor_ID = sensor_ID
        self.range = range 

    def post_reading(self):
        output = random.randint(self.range(0),self.range(1))
        return output


class device_connector():
    def __init__(self, broker, port, patient_ID, topic):

        self.dc = MQTT(broker, port, patient_ID, self)
        self.topic = topic
        self.dc.start()
        self._message = {			
            'patient_ID':'',
            'e':[]
			}

        self._sensors = []

        sensors = json.loads(requests.get('catalog','sensors del paziente n').text)

        for sensor in sensors:

            self._sensors.append(sensor_def(sensor['sensor_type'],sensor['sensor_ID'],sensor['range']))

            self._message['e'].append({
                'n':sensor['sensor_ID'],
                'vs':sensor['sensor_type'],
                'value':'',
                'timestamp':'',
                'unit':''
            })

    # def get_readings(self ,sensor_ID): 

    #     for sensor,n in enumerate(self._message['e']): 

    #         if sensor['sensor_ID'] == sensor_ID:
    #             value = self._sensors[n].post_reading()
    #             self._message['e'][n] = value
    #             break

    def get_readings(self): 

        for sensor,n in enumerate(self._sensors): 

            value = sensor.post_reading()
            self._message['e'][n] = value

        
    def send(self):
        self.dc.my_publish(self.topic, self._message)


if __name__ == '__main__':

    #capire bene come strutturare questa parte qui (prendere dal sensor_type il sensore)

    pat_stats = json.loads(requests.get('catalog','sensors del paziente n').text)
    device_connector1 = device_connector(broker, port, patient_ID, topic)
    pat_stats = json.loads(requests.get('catalog','sensors del paziente n').text)
    device_connector2 = device_connector(broker, port, patient_ID, topic)

    while True:

        device_connector1.get_readings()
        device_connector1.send()

        # device_connector1.post('1',random.randomint())
        # device_connector1.post('2',random.rand())
        # device_connector1.post('3',random.rand())
        # device_connector1.post('4',random.rand())
        # device_connector1.send()

        # device_connector2.post('6',random.rand())
        # device_connector2.post('7',random.rand())
        # device_connector2.post('8',random.rand())
        # device_connector2.send()