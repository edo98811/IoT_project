from MyMQTT import *
import json
import time

class Clinica1:
	def __init__(self, clientID, topic,broker,port):
		self.clinican=MyMQTT(clientID,broker,port,self)
		self.topic=topic

	def start (self):
		self.clinican.start()
		self.clinican.mySubscribe(self.topic)

	def stop (self):
		self.clinican.stop()

	def notify(self, topic, msg):
		msg=json.loads(msg)
		patientID=msg['p_ID']
		latitudine=msg['latitudine']
		longitudine=msg['longitudine']
		problema=msg['problema']
		print(f'ATTENZIONE!\nIl paziente {patientID} sta male soffre di {problema}\n mandare un ambulanza alle coordinate lat:{latitudine}, log:{longitudine}')


if __name__=='__main__':
	#dati= json.load(open('settings_as.json','r'))
	#dati=dati['clinician']
	broker='test.mosquitto.org'
	topic='allert/clinica1'
	port=8086
	service_ID='Clinica1'
	clinican=Clinica1(service_ID,topic,broker,port)
	clinican.start()

	while True:
		time.sleep(1)
	clinica.stop()