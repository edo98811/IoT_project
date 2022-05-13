import json
import paho.mqtt.client as  mqtt_client

class MQTT():
    def __init__(self,name, broker, port, notifier):
        self.name = name
        self.broker = broker
        self.port = int(port)
        self.mqtt_service = mqtt_client.Client(name,True)
        self.notifier = notifier
        self.topic = ""

        self._is_subscriber = True
        self.mqtt_service.on_connect = self.my_on_connect
        self.mqtt_service.on_message = self.my_on_message

    def my_on_connect (self, paho_mqtt, userdata, flags, rc):
        print ("Connected to %s with result code: %d" % (self.broker, rc))

    def my_on_message (self, paho_mqtt , userdata, msg):
        self.notifier.notify (msg.topic, msg.payload)
 
    def my_publish (self, topic, msg):
        self.mqtt_service.publish(topic, json.dumps(msg), 2)
        print ("message to: %s" % (topic))

    def my_subscribe (self, topic):
        self.mqtt_service.subscribe(topic, 2) 
        self._is_subscriber = True
        self.topic = topic
        print ("subscribed to %s" % (topic))
 
    def start(self):
        self.mqtt_service.connect(self.broker , self.port)
        self.mqtt_service.loop_start()

    def unsubscribe(self):
        if (self._is_subscriber):
            self.mqtt_service.unsubscribe(self._topic)
            print ("unsubscribed")
            
    def stop (self):
        if (self._is_subscriber):
            self.mqtt_service.unsubscribe(self._topic)
            print ("unsubscribed")
 
        self.mqtt_service.loop_stop()
        self.mqtt_service.disconnect()