import json
import paho.mqtt.client as mqtt_client

class MQTT():
    def __init__(self, broker, port, name, notifier):
        self.name = name
        self.broker = broker
        self.port = port
        self.mqtt_service = mqtt_client.Client(name,True)
        self.notifier = notifier

        self._is_subscriber = True
        self._paho_mqtt.on_connect = self.my_on_connect
        self._paho_mqtt.on_message = self.my_on_message

    def my_on_connect (self, paho_mqtt, userdata, flags, rc):
        print ("Connected to %s with result code: %d" % (self.broker, rc))

    def my_on_message (self, paho_mqtt , userdata, msg):
        self.notifier.notify (msg.topic, msg.payload)
 
    def my_publish (self, topic, msg):
        self._paho_mqtt.publish(topic, json.dumps(msg), 2)

    def my_subscribe (self, topic):
        self._paho_mqtt.subscribe(topic, 2) 
        self._is_subscriber = True
        self.topic = topic
        print ("subscribed to %s" % (topic))
 
    def start(self):
        self._paho_mqtt.connect(self.broker , self.port)
        self._paho_mqtt.loop_start()

    def unsubscribe(self):
        if (self._is_subscriber):
            self._paho_mqtt.unsubscribe(self._topic)
            
    def stop (self):
        if (self._is_subscriber):
            self._paho_mqtt.unsubscribe(self._topic)
 
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()