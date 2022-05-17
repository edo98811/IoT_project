from MyMQTT import MyMQTT
import json
import time
import requests as r

class Clinica1(object):					#Subscriber Clinica Alert
	def __init__(self, clientID, topic,broker,port):
		self.clinican=MyMQTT(clientID,broker,port,self)
		self.topic=topic

	def start (self):
		self.clinican.start()
		self.clinican.mySubscribe(self.topic)



	def notify(self,topic, msg):
		msg=json.loads(msg)
		patientID=msg['p_ID']
		latitudine=msg['patient_location']['latitude']
		longitudine=msg['patient_location']['longitude']
		problema=msg['patient_problem']
		doctor=msg['doctor_name']
		chat_id=msg['chat_ID']
		print(f'ATTENTION!\n The patient {patientID} needs an ambulance at the coordinates lat:{latitudine} long:{longitudine}!\n Suffers from {problema} , contact his Doctor {doctor} chat ID number:{chat_id}')
		print(f'\n https://www.latlong.net/c/?lat={latitudine}&long={longitudine}')

if __name__=='__main__':
	# dati= json.load(open("settings_as.json","r"))
	# topic = dati['topic']
	# broker = dati['broker']
	# port = dati['port']
	# service_ID = dati['service_ID']

####       CODICE DI "DEBUG"                                                            # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
	with open("../Catalog/catalog.json",'r') as f:                                               # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
		cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
	host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
	port = cat["base_port"]
	catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]

####
  
    # Ottiene dal catalog l'indirizzo del servizio di location
    # s = requests.session() # session non dovrebbe servire a noi: https://realpython.com/python-requests/#the-session-object
	connection_settings = json.loads(r.get(catalog_address +"/get_service_info?", params = {'service_ID':'alert_service'}).text)
	mqtt_broker = r.get(catalog_address +"/get_MQTT").text
	info_clinics=json.loads(r.get(catalog_address +"/get_clinics").text)

	while True:
		k=0
		name_clinics=input('Welcome!\n Write the name of clinics:')
		for p in info_clinics:
			if p['name']==name_clinics:
				k=1
				print('Your clinics is subscriber!')
				# carica i dati relativi al client MQTT e agli indirizzi del location service e del catalog manager
				topic = (connection_settings['topic'].split('/'))[0]+'/'+p["clinic_ID"]
				broker = mqtt_broker
				port = connection_settings['port']
				service_ID = p["clinic_ID"]

				c=Clinica1(service_ID,topic,broker,port)
				c.start()

				done=False
				while not done:
					time.sleep(1)
		if k==0:
			print('The clinics is not subscriber!')
			


 